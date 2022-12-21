from .utils import *
from .syntax import *
from . import sourcematch as sm
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
	__blocksEnds   = None
	__scopes       = None
	

	def __init__(self, filename=None):
		if filename:
			self.load(filename)


	def _matchShellCopy(self):
		srcShell = SourceFile()
		srcShell.__filename  = self.__filename
		srcShell.__lineJoins = self.__lineJoins.copy()
		srcShell.__lineJoinsOrg = self.__lineJoinsOrg.copy()
		srcShell.__lineEnds  = self.__lineEnds.copy()
		return srcShell


	def filename(self):
		return self.__filename


	def load(self, filename, encoding="utf-8"):
		self.__filename = filename
		with open(filename, "r", encoding=encoding, newline="") as f:
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
			assert not os.path.exists(backupName), "File already exists in the backup directory"
			shutil.copy2(filename, backupName)
		with open(filename, "w", encoding=encoding, newline="") as f:
			f.write(self.__lineDisjoinedCode())
			f.flush()
			self.__filename = filename


	def releaseCode(self):
		self.__code = None


	def resetScopes(self):
		self.__scopes = [(None, None)]


	def scopes(self):
		return self.__scopes


	def setScope(self, begin, end):
		self.__scopes = [(begin, end)]


	def setScopes(self, scopes):
		if type(scopes) is tuple: 
			self.__scopes = [scopes]
		else:
			assert type(scopes) is list
			self.__scopes = scopes.copy()


	def addScope(self, begin, end):
		insertRangeSorted(self.__scopes, begin, end)


	def isClipped(self, pos):
		for (start, end, _) in self.__clipRanges:
			if start > pos:
				return False
			elif end > pos:
				return True
		return False
	

	# result - generator
	def __findAllGenUnscoped(self, pat, begin, end, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = regex.compile(pat)
		for mres in pat.finditer(self.__code, begin, end):
			if not excludeClips or not self.isClipped(mres.start()):
				yield mres
	

	# result - generator
	def __findAllGen(self, pat, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = regex.compile(pat)
		for (begin, end) in self.__scopes:
			for mres in pat.finditer(self.__code, begin, end):
				if not excludeClips or not self.isClipped(mres.start()):
					yield mres


	# result - generator
	def __findAllGen_SkipBlocks(self, pat, excludeClips=True):
		if pat is regex.Pattern: 
			pat = pat.pattern
		pat += r"|\{"
		pat = regex.compile(pat)
		for (begin, end) in self.__scopes:
			while mres := pat.search(self.__code, begin, end):
				if mres.group(0) == "{":
					begin = self.__blocksEnds[mres.start()] + 1
				elif not excludeClips or not self.isClipped(mres.start()):
					begin = mres.end()
					yield mres
				

	def __matchReUnscoped(self, re, begin, end=None, excludeClips=True):
		pat = regex.compile(re)
		return self.__matchPatUnscoped(pat, begin, end, excludeClips)


	def __matchPatUnscoped(self, pat, begin, end=None, excludeClips=True):
		while mres := pat.match(self.__code, begin, end):
			if not excludeClips or not self.isClipped(mres.start()):
				return mres
			else:
				begin = mres.end()
				

	def __findReUnscoped(self, re, begin, end=None, excludeClips=True):
		pat = regex.compile(re)
		return self.__findReUnscoped(pat, begin, end, excludeClips)


	def __findPatUnscoped(self, pat, begin, end=None, excludeClips=True):
		while mres := pat.search(self.__code, begin, end):
			if not excludeClips or not self.isClipped(mres.start()):
				return mres
			else:
				begin = mres.end()
			

	def __findReUnscoped_SkipBlocks(self, re, begin, end=None, excludeClips=True):
		pat = regex.compile(re + r"|\{")
		return self.__findPatUnscoped_SkipBlocks(pat, begin, end, excludeClips)

				
	# pat has to already include "|\{"
	def __findPatUnscoped_SkipBlocks(self, pat, begin, end=None, excludeClips=True):
		while mres := pat.search(self.__code, begin, end):
			if excludeClips and self.isClipped(mres.start()):
				begin = mres.end()
			elif mres.group() == "{":
				begin = self.__blocksEnds[mres.start()] + 1
			else:
				return mres


	def __find(self, pat, excludeClips=True):
		return next(self.__findAllGen(pat, excludeClips), None)
	

	def __find_SkipBlocks(self, pat, excludeClips=True):
		return next(self.__findAllGen_SkipBlocks(pat, excludeClips), None)
	

	def matchUnscoped(self, pat, begin=None, end=None, *, excludeClips=True):
		if begin is not None: begin = self._relPos(begin)
		if end   is not None: end   = self._relPos(end)
		if type(pat) is regex.Pattern:
			mres = self.__matchPatUnscoped(pat, begin, end, excludeClips)
		else:
			mres = self.__matchReUnscoped(pat, begin, end, excludeClips)
		return sm.SourceMatch(self, mres) if mres else None


	def findUnscoped(self, pat, begin=None, end=None, *, excludeClips=True):
		if begin is not None: begin = self._relPos(begin)
		if end   is not None: end   = self._relPos(end)
		if type(pat) is regex.Pattern:
			mres = self.__findPatUnscoped(pat, begin, end, excludeClips)
		else:
			mres = self.__findReUnscoped(pat, begin, end, excludeClips)
		return sm.SourceMatch(self, mres) if mres else None


	def findUnscoped_SkipBlocks(self, pat, begin=None, end=None, *, excludeClips=True):
		assert type(pat) is not regex.Pattern
		if begin is not None: begin = self._relPos(begin)
		if end   is not None: end   = self._relPos(end)
		mres = self.__findReUnscoped_SkipBlocks(pat, begin, end, excludeClips)
		return sm.SourceMatch(self, mres) if mres else None


	def find(self, pat, *, excludeClips=True):
		if mres := self.__find(pat, excludeClips):
			return sm.SourceMatch(self, mres)
		else:
			return None
		

	def find_SkipBlocks(self, pat, begin=None, end=None, *, excludeClips=True):
		if mres := next(self.__find_SkipBlocks(pat, begin, end, excludeClips), None):
			return sm.SourceMatch(self, mres)
		else:
			return None
		

	# result - generator
	def findAllGen(self, pat, *, excludeClips=True):
		gen = self.__findAllGen(pat, excludeClips)
		srcMatchCopy = self._matchShellCopy()
		while mres := next(gen, None):
			yield sm.SourceMatch(srcMatchCopy, mres, copySource=False)
			

	# result - generator
	def findAllGen_SkipBlocks(self, pat, *, excludeClips=True):
		gen = self.__findAllGen_SkipBlocks(pat, excludeClips)
		srcMatchCopy = self._matchShellCopy()
		while mres := next(gen, None):
			yield sm.SourceMatch(srcMatchCopy, mres, copySource=False)
		

	# result - generator
	def findAllGenUnscoped(self, pat, begin=None, end=None, *, excludeClips=True):
		gen = self.__findAllGenUnscoped(pat, begin, end, excludeClips)
		srcMatchCopy = self._matchShellCopy()
		while mres := next(gen, None):
			yield sm.SourceMatch(srcMatchCopy, mres, copySource=False)


	def replaceMatch(self, m, repl):
		self.replaceMatches([m], repl)

		#if type(m) is sm.SourceMatch:
		#	m = m._SourceMatch__mres
		#if callable(repl):
		#	repl = repl(m)
		#self.__code = "".join([self.__code[:m.start()], repl, self.__code[m.end():]])
		#self.__shiftAndClearLineJoins( [(m.start(), m.end(), len(repl) - len(m.group(0)))] )
		#self.recalcCode()


	def replaceMatches(self, ms, repl, *, sorted=False):
		if not sorted:
			ms.sort(key=lambda m: (m.start(), m.end()))
		if type(repl) is str:
			repl = lambda _: repl
		shifts = []
		newCode = []
		chunkBegin = 0
		for m in ms:
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
		if scopes:
			oldScopes = self.__scopes
			self.setScopes(scopes)

		if mres := self.__find(Syntax.makeClassPrefixRe(cname)):
			begin = mres.end()
			self.setScope(begin, self.__blocksEnds[begin - 1])
			return self._orgPos(mres.start())
		else:
			if scopes: self.__scopes = oldScopes
			return -1


	# scope file to all bodis of the namespace nsname that start in the given scopes or in
	# the currently active scopes if given None
	def tryScopeToNamespaceBodies(self, nsname, scopes=None):
		if scopes:
			oldScopes = self.__scopes
			self.setScopes(scopes)

		nsPrefixRe = Syntax.makeNamespacePrefixRe(nsname)
		nsScopes = []

		pos = 0
		for (begin, end) in self.__scopes:
			if begin is not None and pos < begin: 
				pos = begin
			while (end is None or pos < end) and (mres := self.__findReUnscoped_SkipBlocks(nsPrefixRe, pos, end)):
				pos = mres.end()
				insertRangeSorted(nsScopes, pos, self.__blocksEnds[pos - 1])
				pos = self.__blocksEnds[pos - 1] + 1

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
		self.__blocksEnds = {}
		pos = 0
		begins = []
		while mres := self.__findPatUnscoped(SourceFile.__blockEdgePat, pos):
			match mres.group():
				case '{': 
					begins.append(mres.start())
				case '}': 
					assert begins, f"{self.__filename}:{self._orgPos(pos)}: }} has no match."
					self.__blocksEnds[begins.pop()] = mres.start()
			pos = mres.end()

		assert begins == [], f"{self.__filename}{self._orgPos(begins[-1])}: {{ has no match."


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
		newLineJoinsOrg = []
		joinPos = len(self.__lineJoins) - 1
		for (begin, end, shift) in reversed([(0, 0, 0)] + shifts):
			while joinPos >= 0 and end <= self.__lineJoins[joinPos]:
				newLineJoins.append(self.__lineJoins[joinPos] + shift)
				newLineJoinsOrg.append(self.__lineJoinsOrg[joinPos] + shift)
				joinPos -= 1
			while joinPos >= 0 and begin <= self.__lineJoins[joinPos]:
				joinPos -= 1

		self.__lineJoins = numpy.array(list(reversed(newLineJoins)))
		self.__lineJoinsOrg = numpy.array(list(reversed(newLineJoinsOrg)))


	def _orgPos(self, pos):
		return pos + 3*self._lineJoinsBefore(pos)
	

	def _relPos(self, pos):
		return pos - 3*self._lineJoinsOrgBefore(pos)


	def _intLocation(self, pos):
		ln = numpy.searchsorted(self.__lineEnds, pos, 'right')
		col = pos - self.__lineEnds[ln-1] if ln > 0 else pos
		return (ln, col)
	

	def _intOrgLocation(self, pos):
		ln = numpy.searchsorted(self.__lineEnds, pos, 'right')
		lnStart = self.__lineEnds[ln-1] if ln > 0 else 0
		if joinsBefore := self._lineJoinsBefore(pos):
			lastJoin = self.__lineJoins[joinsBefore-1]
			lnStart = max(lnStart, lastJoin)
		return (ln + joinsBefore, pos - lnStart)
