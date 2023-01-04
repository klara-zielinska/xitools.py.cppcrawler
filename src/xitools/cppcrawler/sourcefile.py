from dataclasses import replace
from .utils import *
from .syntax import *
from . import sourcematch as sm
from copy import copy
import numpy
import shutil
import errno
import os


class SourceFile:
	__filename     = None
	__code         = None
	__lineJoins    = None
	__lineJoinsOrg = None
	__clipRanges   = None
	__lineEnds     = None
	__blockEnds    = None
	__scopes       = None
	

	def __init__(self, filename=None):
		if filename:
			self.load(filename)
			
        
	def __str__(self):
		return (f"<xitools.cppcrawler.sourcefile.SourceFile object at {hex(id(self))}, "
			    f"filename='{self.filename()}'>")


	__repr__ = __str__


	# returns internal code representation
	def _intCode(self):
		return self.__code


	def code(self, start=None, end=None):
		return self.__code[self._intPos(start):self._intPos(end)]


	def copy(self):
		cp = SourceFile()
		cp.__filename   = self.__filename
		cp.__code       = self.__code
		cp.__lineJoins  = self.__lineJoins.copy()
		cp.__lineJoinsOrg = self.__lineJoinsOrg.copy()
		cp.__clipRanges = self.__clipRanges.copy()
		cp.__lineEnds   = self.__lineEnds.copy()
		cp.__blockEnds  = self.__blockEnds.copy()
		cp.__scopes     = self.__scopes.copy()
		return cp


	def filename(self):
		return self.__filename


	def load(self, filename, encoding="utf-8"):
		self.__filename = os.path.abspath(filename)
		with open(self.__filename, "r", encoding=encoding, newline="") as f:
			self.__code = f.read()
			self.__joinLines()
			self.resetScopes()
			self.recalcCode()


	def recalcCode(self):
		self.__makeClipRangesAndLineEnds()
		self.__makeBlockEnds()


	def save(self, encoding="utf-8", *, backupDir=None, force=False):
		self.saveAs(self.__filename, encoding, backupDir=backupDir, force=force)


	def saveAs(self, filename, encoding="utf-8", *, backupDir=None, force=False):
		assert self.__filename, "No file name."
		if os.path.exists(filename) and not force:
			raise FileExistsError(errno.EEXIST, "File exists, use force to override", filename)
		if backupDir:
			backupName = os.path.join(backupDir, os.path.basename(filename))
			if os.path.exists(backupName): 
				raise FileExistsError(errno.EEXIST, "Backup file already exists", backupName)
			shutil.copy2(filename, backupName)
		with open(filename, "w", encoding=encoding, newline="") as f:
			f.write(self.__lineDisjoinedCode())
			f.flush()
			self.__filename = filename


	def releaseCode(self):
		self.__code = None


	def resetScopes(self):
		self.__scopes = [(None, None)]


	def _intScopes(self):
		return self.__scopes


	def setScope(self, begin, end):
		self.__scopes = [(self._intPos(begin), self._intPos(end))]


	def setScopes(self, scopes):
		if type(scopes) is tuple:
			scopes = [scopes]
		assert type(scopes) is list
		self.__scopes = list(map(lambda scope: (self._intPos(scope[0]), self._intPos(scope[1])), scopes))


	def addScope(self, begin, end):
		insertRangeSorted(self.__scopes, self._intPos(begin), self._intPos(end))


	def isClipped(self, pos):
		for (start, end, _) in self.__clipRanges:
			if start > pos:
				return False
			elif end > pos:
				return True
		return False
	

	# result - generator
	def __findAllPatGen_Unscoped(self, pat, begin, end, excludeClips=True):
		for mres in pat.finditer(self.__code, begin, end):
			if not excludeClips or not self.isClipped(mres.start()):
				yield mres
	

	# result - generator
	def __findAllPatGen_Unscoped_SkipBlocks(self, pat, begin, end, excludeClips=True):
		while mres := pat.search(self.__code, begin, end):
			if mres.group("__cppcr_sbo"):
				if self.isClipped(mres.start()):
					begin = mres.end()
				else:
					begin = self.__blockEnds[mres.start()]
			else:
				begin = mres.end()
				if not excludeClips or not self.isClipped(mres.start()):
					yield mres


	# result - generator
	def __findAllPatGen(self, pat, excludeClips=True):
		for (begin, end) in self.__scopes:
			for mres in pat.finditer(self.__code, begin, end):
				if not excludeClips or not self.isClipped(mres.start()):
					yield mres


	# result - generator
	def __findAllPatGen_SkipBlocks(self, pat, excludeClips=True):
		for (begin, end) in self.__scopes:
			while mres := pat.search(self.__code, begin, end):
				if mres.group("__cppcr_sbo"):
					if self.isClipped(mres.start()):
						begin = mres.end()
					else:
						begin = self.__blockEnds[mres.start()]
				else:
					begin = mres.end()
					if not excludeClips or not self.isClipped(mres.start()):
						yield mres


	def __matchPatUnscoped(self, pat, begin, end=None, excludeClips=True):
		while mres := pat.match(self.__code, begin, end):
			if not excludeClips or not self.isClipped(mres.start()):
				return mres
			else:
				begin = mres.end()


	def __findPatUnscoped(self, pat, begin, end=None, excludeClips=True):
		while mres := pat.search(self.__code, begin, end):
			if not excludeClips or not self.isClipped(mres.start()):
				return mres
			else:
				begin = mres.end()

				
	# pat has to be prepared with makeSkipBlocksPat (suffixed with "|(?P<__cppcr_sbo>\{)")
	def __findPatUnscoped_SkipBlocks(self, pat, begin, end=None, excludeClips=True):
		while mres := pat.search(self.__code, begin, end):
			if mres.group("__cppcr_sbo"):
				if self.isClipped(mres.start()):
					begin = mres.end()
				else:
					begin = self.__blockEnds[mres.start()]
			else:
				begin = mres.end()
				if not excludeClips or not self.isClipped(mres.start()):
					return mres


	def __findPat(self, pat, excludeClips=True):
		return next(self.__findAllPatGen(pat, excludeClips), None)
	

	def __findPat_SkipBlocks(self, pat, excludeClips=True):
		return next(self.__findAllPatGen_SkipBlocks(pat, excludeClips), None)
	

	def matchUnscoped(self, pat, begin=None, end=None, *, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = regex.compile(pat)
		if begin is not None: begin = self._intPos(begin)
		if end   is not None: end   = self._intPos(end)
		mres = self.__matchPatUnscoped(pat, begin, end, excludeClips)
		return sm.SourceMatch(self, mres) if mres else None


	def findUnscoped(self, pat, begin=None, end=None, *, skipBlocks=False, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = SourceFile.makeSkipBlocksPat(pat) if skipBlocks else regex.compile(pat)
		else:
			assert not skipBlocks or SourceFile.checkSkipBlocksPat(pat)
		if begin is not None: begin = self._intPos(begin)
		if end   is not None: end   = self._intPos(end)

		if skipBlocks: mres = self.__findPatUnscoped_SkipBlocks(pat, begin, end, excludeClips)
		else:          mres = self.__findPatUnscoped(pat, begin, end, excludeClips)
		return sm.SourceMatch(self, mres) if mres else None
		

	def find(self, pat, *, skipBlocks=False, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = SourceFile.makeSkipBlocksPat(pat) if skipBlocks else regex.compile(pat)
		else:
			assert not skipBlocks or SourceFile.checkSkipBlocksPat(pat)

		if skipBlocks: mres = self.__findPat_SkipBlocks(pat, excludeClips)
		else:          mres = self.__findPat(pat, excludeClips)
		if mres: return sm.SourceMatch(self, mres)
		else:    return None
			
		
	# if skipBlocks, pat has to be prepared with makeSkipBlocksPat (suffixed with "|(?P<__cppcr_sbo>\{)")
	# result - generator
	def findAllGen(self, pat, *, skipBlocks=False, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat =SourceFile.makeSkipBlocksPat(pat) if skipBlocks else  regex.compile(pat)
		else:
			assert not skipBlocks or SourceFile.checkSkipBlocksPat(pat)
		srcMatchCopy = self.copy()

		if skipBlocks: gen = self.__findAllPatGen_SkipBlocks(pat, excludeClips)
		else:          gen = self.__findAllPatGen(pat, excludeClips)
		while mres := next(gen, None):
			yield sm.SourceMatch(srcMatchCopy, mres, copySource=False)
		
			
	# if skipBlocks, pat has to be prepared with makeSkipBlockPat (suffixed with "|(?P<__cppcr_sbo>\{)")
	# result - generator
	def findAllGen_Unscoped(self, pat, begin=None, end=None, *, skipBlocks=False, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = SourceFile.makeSkipBlocksPat(pat) if skipBlocks else regex.compile(pat)
		else:
			assert not skipBlocks or SourceFile.checkSkipBlocksPat(pat)
		srcMatchCopy = self.copy()
		
		if skipBlocks: gen = self.__findAllPatGen_Unscoped_SkipBlocks(pat, begin, end, excludeClips)
		else:		   gen = self.__findAllPatGen_Unscoped(pat, begin, end, excludeClips)
		while mres := next(gen, None):
			yield sm.SourceMatch(srcMatchCopy, mres, copySource=False)


	def replaceMatch(self, match, repl):
		self.replaceMatches([match], repl)


	# the result is going to be invalid if matches are not sorted and the parameter sorted=True
	def replaceMatches(self, matches, repl, *, sorted=False):
		if not sorted:
			matches.sort(key=lambda m: (m.start(), m.end()))
		if type(repl) is str:
			_repl = repl
			repl = lambda _: _repl
		shifts = []
		newCode = []
		chunkBegin = 0
		for m in matches:
			m = m._SourceMatch__mres
			newCode.append(self.__code[chunkBegin:m.start()])
			replStr = repl(m)
			assert "\\\r\n" not in replStr
			newCode.append(replStr)
			chunkBegin = m.end()
			shifts.append((m.start(), m.end(), len(replStr) - len(m.group(0))))
		newCode.append(self.__code[chunkBegin:])
		self.__code = "".join(newCode)
		self.__shiftAndClearLineJoins(shifts)
		self.recalcCode()


	def replaceAll(self, pat, repl, *, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = regex.compile(pat)
		if type(repl) is str:
			_repl = repl
			repl = lambda _: _repl
		shifts = []

		def inRepl(mres):
			if excludeClips and self.isClipped(mres.start()):
				return mres.group(0)
			else:
				repStr = repl(mres)
				assert "\\\r\n" not in repStr
				shifts.append( (mres.start(), mres.end(), len(repStr) - len(mres.group(0))) )
				return repStr

		for (begin, end) in self.__scopes:
			self.__code = pat.sub(inRepl, self.__code, pos=begin, endpos=end)
		self.__shiftAndClearLineJoins(shifts)
		self.recalcCode()


	# heuristic selection of the body of the given class
	# selection = scoping to
	# return: the position of the class definition or -1 in none
	def tryScopeToClassBody(self, cname, scopes=None):
		return self.__tryScopeToBlockByPrefix(Syntax.makeClassPrefixRe(f"(?:{cname})"), scopes)
		

	# scope file to all bodis of the namespace nsname that start in the given scopes or in
	# the currently active scopes if given None
	def tryScopeToNamespaceBody(self, nsname, scopes=None):
		return self.__tryScopeToBlockByPrefix(Syntax.makeNamespacePrefixRe(f"(?:{nsname})"), scopes)


	def lineStart(self, pos):
		ln = self._intLineNo(self._intPos(pos))
		return self._orgPos(0 if ln == 0 else self.__lineEnds[ln - 1])


	def findFirstBlock(self, pos):
		if mres := self.__findPatUnscoped(regex.compile("{"), self._intPos(pos)):
			return (self._orgPos(mres.start()), self._orgPos(self.__blockEnds[mres.start()] + 1))
		else:
			return None
	

	def __tryScopeToBlockByPrefix(self, prefixRe, scopes=None):
		if scopes:
			oldScopes = self.__scopes
			self.setScopes(scopes)

		nsPrefixPat = SourceFile.makeSkipBlocksPat(prefixRe)
		nsScopes = []

		pos = 0
		for scope in self.__scopes:
			begin = scope[0]
			end   = scope[1]
			if tagged := len(scope) == 3:
				tag = scopes[2]
			if begin is not None and pos < begin: 
				pos = begin
			while (end is None or pos < end) and (mres := self.__findPatUnscoped_SkipBlocks(nsPrefixPat, pos, end)):
				pos = mres.end()
				foundScope = tuple([pos, self.__blockEnds[pos - 1]] + ([tag] if tagged else []))
				nsScopes.append(foundScope)
				pos = self.__blockEnds[pos - 1] + 1

		if nsScopes:
			self.__scopes = nsScopes
			return True
		else:
			if scopes: self.__scopes = oldScopes
			return False
	

	def __makeClipRangesAndLineEnds(self):
		self.__clipRanges = []
		self.__lineEnds = []

		pos = 0
		while (res := Syntax.nextClipAndLineEnds(self.__code, pos)) and (clip := res[0]):
			pos = clip[1] + (2 if clip[2] == 'C' else 1)
			self.__clipRanges.append(clip)
			self.__lineEnds.extend(res[1])
		self.__lineEnds.extend(res[1])

		#self.__clipRanges = numpy.array(self.__clipRanges)
		self.__lineEnds = numpy.array(self.__lineEnds)


	# method consts:
	__blockEdgePat = regex.compile(r"[\{}]")

	def __makeBlockEnds(self):
		self.__blockEnds = {}
		pos = 0
		begins = []
		while mres := self.__findPatUnscoped(SourceFile.__blockEdgePat, pos):
			match mres.group():
				case '{': 
					begins.append(mres.start())
				case '}': 
					assert begins, f"{self.__filename}:{self._orgPos(pos)}: }} has no match."
					self.__blockEnds[begins.pop()] = mres.start()
			pos = mres.end()

		assert begins == [], f"{self.__filename}:{self._orgPos(begins[-1])}: {{ has no match."


	def __joinLines(self):
		joins = []
		joinsOrg = []
		def onMatch(m):
			joins.append(m.start() - 3*len(joins))
			joinsOrg.append(m.start())
			return ""
		self.__code = regex.sub(r"\\\r\n", onMatch, self.__code)
		self.__lineJoins = numpy.array(joins)
		self.__lineJoinsOrg = numpy.array(joinsOrg)


	def __recalc_lineJoinsOrg(self):
		newLineJoinsOrg = []
		shift = 0
		for pos in self.__lineJoins:
			newLineJoinsOrg.append(pos + shift)
			shift += 3
		self.__lineJoinsOrg = numpy.array(newLineJoinsOrg)


	def __lineDisjoinedCode(self):
		chunkBegin = 0
		chunks = []
		for pos in self.__lineJoins:
			chunks.append(self.__code[chunkBegin:pos])
			chunkBegin = pos
		chunks.append(self.__code[chunkBegin:])
		return "\\\r\n".join(chunks)


	def _lineJoinsBefore(self, pos):
		return numpy.searchsorted(self.__lineJoins, pos, 'right')


	def _lineJoinsOrgBefore(self, pos):
		return numpy.searchsorted(self.__lineJoinsOrg, pos, 'right')


	def __shiftAndClearLineJoins(self, shifts):
		if len(self.__lineJoins) == 0:
			return

		shiftSum = 0
		for i in range(len(shifts)):
			shiftSum += shifts[i][2]
			shifts[i] = (shifts[i][0], shifts[i][1], shiftSum)

		newLineJoins = []
		joinPos = len(self.__lineJoins) - 1
		for (begin, end, shift) in reversed([(0, 0, 0)] + shifts):
			while joinPos >= 0 and end <= self.__lineJoins[joinPos]:
				newLineJoins.append(self.__lineJoins[joinPos] + shift)
				joinPos -= 1
			while joinPos >= 0 and begin <= self.__lineJoins[joinPos]:
				joinPos -= 1

		self.__lineJoins = numpy.array(list(reversed(newLineJoins)))
		self.__recalc_lineJoinsOrg()


	def _intLineNo(self, pos):
		return numpy.searchsorted(self.__lineEnds, pos, 'right')


	def _orgPos(self, pos):
		if pos is None:
			return None
		else:
			return pos + 3*self._lineJoinsBefore(pos)
	

	def _intPos(self, pos):
		if pos is None:
			return None
		else:
			n = self._lineJoinsOrgBefore(pos)
			correct = 0
			if n > 0:
				space = pos - self.__lineJoinsOrg[n - 1]
				correct = 3 - min(space, 3)
			return pos - 3*n + correct


	def _intLocation(self, pos):
		ln = self._intLineNo(pos)
		col = pos - self.__lineEnds[ln-1] if ln > 0 else pos
		return (ln, col)
	

	def _intOrgLocation(self, pos):
		ln = self._intLineNo(pos)
		lnStart = self.__lineEnds[ln-1] if ln > 0 else 0
		if joinsBefore := self._lineJoinsBefore(pos):
			lastJoin = self.__lineJoins[joinsBefore-1]
			lnStart = max(lnStart, lastJoin)
		return (ln + joinsBefore, pos - lnStart)


	def makeSkipBlocksPat(re):
		return regex.compile(re + r"|(?P<__cppcr_sbo>\{)")
