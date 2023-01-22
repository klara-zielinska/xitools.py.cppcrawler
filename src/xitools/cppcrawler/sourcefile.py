from dataclasses import replace
from .utils import *
from .syntax import *
from . import sourcematch as sm
from copy import copy
import numpy
import shutil
import errno
import os


_blockStartPat = regex.compile(
	r"(?:(?P<ts>\s))*"
	r"(?<=\r\n(?P<ind>[ \t]+))?(?P<ins>)(?=.*(?P<preproc>#(?:define|undef|if|ifdef|ifndef|else|endif|pragma)\b))?[^\s].*"
	r"(?:\r\n(?P<ind>[ \t]*))?")

_blockStartSkipComPat = regex.compile(
	r"(?:(?P<ts>\s)|"f"{Syntax.commentRe})*"
	r"(?<=\r\n(?P<ind>[ \t]+))?(?P<ins>)(?=.*(?P<preproc>#(?:define|undef|if|ifdef|ifndef|else|endif|pragma)\b))?[^\s].*"
	r"(?:\r\n(?P<ind>[ \t]*))?")


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


	def intCode(self, start=None, end=None):
		return self.__code[self._intPos(start):self._intPos(end)]


	def filename(self):
		return self.__filename


	def blockEnd(self, begin, *, int=False):
		ibegin = begin if int else self._intPos(begin) 
		return self._orgPos(self.__blockEnds[ibegin])


	def resetScopes(self):
		self.__scopes = [(None, None, None)]


	def _intScopes(self):
		return self.__scopes


	def scopes(self):
		return [ (self._orgPos(begin), self._orgPos(end), tag) for (begin, end, tag) in self.__scopes ]


	def setScope(self, begin, end, tag=None):
		self.__scopes = [(self._intPos(begin), self._intPos(end), tag)]


	def setScopes(self, scopes):
		if type(scopes) is tuple:
			scopes = [scopes]
		assert type(scopes) is list
		self.__scopes = [ (self._intPos(scope[0]), self._intPos(scope[1]), scope[2] if len(scope) == 3 else None)
						  for scope in scopes ]


	#def addScope(self, begin, end, tag=None):
	#	insertRangeSorted(self.__scopes, self._intPos(begin), self._intPos(end))


	def isClippedInt(self, pos):
		for (start, end, _) in self.__clipRanges:
			if start > pos:
				return False
			elif end > pos:
				return True
		return False


	def getClipRangeInt(self, pos):
		for range in self.__clipRanges:
			(start, end, _) = range
			if start > pos:
				return None
			elif end > pos:
				return range
		return None


	def lineStart(self, pos):
		ln = self._intLineNo(self._intPos(pos))
		return self._orgPos(0 if ln == 0 else self.__lineEnds[ln - 1])


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


	def findFirstBlock(self, pos):
		if mres := self.__findPatUnscoped(regex.compile("{"), self._intPos(pos)):
			return (self._orgPos(mres.start()), self._orgPos(self.__blockEnds[mres.start()] + 1))
		else:
			return None
	

	# result - generator
	def __findAllPatGen_Unscoped(self, pat, begin, end, excludeClips=True):
		while mres := pat.search(self.__code, begin, end):
			if excludeClips and (range := self.getClipRangeInt(mres.start())):
				begin = range[1]
			else:
				begin = mres.end()
				yield mres
	

	# result - generator
	def __findAllPatGen_Unscoped_SkipBlocks(self, pat, begin, end, excludeClips=True):
		while mres := pat.search(self.__code, begin, end):
			if mres.group("__cppcr_sbo"):
				if self.isClippedInt(mres.start()):
					begin = mres.end()
				else:
					begin = self.__blockEnds[mres.start()]
			else:
				if excludeClips and (range := self.getClipRangeInt(mres.start())):
					begin = range[1]
				else:
					begin = self._blockExtension(begin, mres.end())
					yield mres


	# result - generator
	def __findAllPatGen(self, pat, excludeClips=True, scopeTag=False):
		if scopeTag: 
			def wrapRes(mres, stag): return (mres, stag)
		else:       
			def wrapRes(mres, stag): return mres

		for (begin, end, stag) in self.__scopes:
			while mres := pat.search(self.__code, begin, end):
				if excludeClips and (range := self.getClipRangeInt(mres.start())):
					begin = range[1]
				else:
					begin = mres.end()
					yield wrapRes(mres, stag)


	# result - generator
	def __findAllPatGen_SkipBlocks(self, pat, excludeClips=True, scopeTag=False):
		if scopeTag: 
			def wrapRes(mres, stag): return (mres, stag)
		else:       
			def wrapRes(mres, stag): return mres

		for (begin, end, stag) in self.__scopes:
			while mres := pat.search(self.__code, begin, end):
				if mres.group("__cppcr_sbo"):
					if self.isClippedInt(mres.start()):
						begin = mres.end()
					else:
						begin = self.__blockEnds[mres.start()]
				else:
					if excludeClips and (range := self.getClipRangeInt(mres.start())):
						begin = range[1]
					else:
						begin = self._blockExtension(begin, mres.end())
						yield wrapRes(mres, stag)


	def __matchPatUnscoped(self, pat, begin, end=None, excludeClips=True):
		if excludeClips and self.getClipRangeInt(begin):
			return None
		else:
			return pat.match(self.__code, begin, end)


	def __fullmatchPatUnscoped(self, pat, begin, end=None, excludeClips=True):
		if excludeClips and self.getClipRangeInt(begin):
			return None
		else:
			return pat.fullmatch(self.__code, begin, end)


	def __findPatUnscoped(self, pat, begin, end=None, excludeClips=True):
		while mres := pat.search(self.__code, begin, end):
			if excludeClips and (range := self.getClipRangeInt(mres.start())):
				begin = range[1]
			else:
				return mres

				
	# pat has to be prepared with makeSkipBlocksPat (suffixed with "|(?P<__cppcr_sbo>\{)")
	def __findPatUnscoped_SkipBlocks(self, pat, begin, end=None, excludeClips=True):
		while mres := pat.search(self.__code, begin, end):
			if mres.group("__cppcr_sbo"):
				if self.isClippedInt(mres.start()):
					begin = mres.end()
				else:
					begin = self.__blockEnds[mres.start()]
			else:
				if excludeClips and (range := self.getClipRangeInt(mres.start())):
					begin = range[1]
				else:
					return mres


	def __findPat(self, pat, excludeClips=True, scopeTag=False):
		return next(self.__findAllPatGen(pat, excludeClips, scopeTag), None)
	

	def __findPat_SkipBlocks(self, pat, excludeClips=True, scopeTag=False):
		return next(self.__findAllPatGen_SkipBlocks(pat, excludeClips, scopeTag), None)
	

	def matchUnscoped(self, pat, begin=0, end=None, *, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = regex.compile(pat)
		if begin is not None: begin = self._intPos(begin)
		if end   is not None: end   = self._intPos(end)
		mres = self.__matchPatUnscoped(pat, begin, end, excludeClips)
		return sm.SourceRegexMatch(self, mres) if mres else None
	

	def fullmatchUnscoped(self, pat, begin=0, end=None, *, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = regex.compile(pat)
		if begin is not None: begin = self._intPos(begin)
		if end   is not None: end   = self._intPos(end)
		mres = self.__fullmatchPatUnscoped(pat, begin, end, excludeClips)
		return sm.SourceRegexMatch(self, mres) if mres else None


	def findUnscoped(self, pat, begin=None, end=None, *, skipBlocks=False, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = SourceFile.makeSkipBlocksPat(pat) if skipBlocks else regex.compile(pat)
		else:
			assert not skipBlocks or SourceFile.checkSkipBlocksPat(pat)
		if begin is not None: begin = self._intPos(begin)
		if end   is not None: end   = self._intPos(end)

		if skipBlocks: mres = self.__findPatUnscoped_SkipBlocks(pat, begin, end, excludeClips)
		else:          mres = self.__findPatUnscoped(pat, begin, end, excludeClips)
		return sm.SourceRegexMatch(self, mres) if mres else None
		

	def find(self, pat, *, skipBlocks=False, scopeTag=False, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = SourceFile.makeSkipBlocksPat(pat) if skipBlocks else regex.compile(pat)
		else:
			assert not skipBlocks or SourceFile.checkSkipBlocksPat(pat)

		if skipBlocks: timres = self.__findPat_SkipBlocks(pat, excludeClips, scopeTag)
		else:          timres = self.__findPat(pat, excludeClips, scopeTag)
		if not timres: return None
		elif scopeTag:
			mres = sm.SourceRegexMatch(self, timres[0])
			return (mres, timres[1])
		else:       
			return sm.SourceRegexMatch(self, timres)
			
		
	# if skipBlocks, pat has to be prepared with makeSkipBlocksPat (suffixed with "|(?P<__cppcr_sbo>\{)")
	# result - generator
	def findAllGen(self, pat, *, skipBlocks=False, scopeTag=False, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat =SourceFile.makeSkipBlocksPat(pat) if skipBlocks else  regex.compile(pat)
		else:
			assert not skipBlocks or SourceFile.checkSkipBlocksPat(pat)
		srcMatchCopy = self.copy()
		if scopeTag:
			def wrapRes(timres):
				mres = sm.SourceRegexMatch(srcMatchCopy, timres[0], copySource=False)
				return (mres, timres[1])
		else:       
			def wrapRes(imres):
				return sm.SourceRegexMatch(srcMatchCopy, imres, copySource=False)
		
		if skipBlocks: gen = self.__findAllPatGen_SkipBlocks(pat, excludeClips, scopeTag)
		else:          gen = self.__findAllPatGen(pat, excludeClips, scopeTag)
		while tmres := next(gen, None):
			yield wrapRes(tmres)
		
			
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
			yield sm.SourceRegexMatch(srcMatchCopy, mres, copySource=False)


	def replaceMatch(self, match, repl):
		self.replaceMatches([match], repl)


	# the result is going to be invalid if matches are not sorted and the parameter sorted=True
	def replaceMatches(self, matches, repl, *, sorted=False):
		if not matches:
			return
		if not sorted:
			matches.sort()
		if type(repl) is str:
			_repl = repl
			repl = lambda _: _repl
		if type(matches[0]) == tuple: # is tagged
			def getMres(tm): return tm[0]
		else:
			def getMres(m): return m
		shifts = []
		newCode = []
		chunkBegin = 0
		for tm in matches:
			mres = getMres(tm)
			newCode.append(self.__code[chunkBegin:mres._intStart()])
			replStr = repl(tm)
			assert "\\\r\n" not in replStr
			newCode.append(replStr)
			chunkBegin = mres._intEnd()
			shifts.append((mres._intStart(), mres._intEnd(), len(replStr) - len(mres.group(0))))
		newCode.append(self.__code[chunkBegin:])
		self.__code = "".join(newCode)
		self.__shiftAndClearLineJoins(shifts)
		self.recalcCode()


	def replaceRange(self, begin, end, repl):
		self.replaceMatch(sm.SourceRangeMatch(self, (begin, end)), repl)


	def replace(self, pat, repl, count=0, *, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = regex.compile(pat)
		if type(repl) is str:
			_repl = repl
			repl = lambda _: _repl
		shifts = []

		def inRepl(mres):
			if excludeClips and self.isClippedInt(mres.start()):
				return mres.group(0)
			else:
				repStr = repl(mres)
				assert "\\\r\n" not in repStr
				shifts.append( (mres.start(), mres.end(), len(repStr) - len(mres.group(0))) )
				return repStr

		replaced = 0 
		for (begin, end, _) in self.__scopes:
			actCount = 0 if count == 0 else count - replaced
			(self.__code, foundCount) = pat.subn(inRepl, self.__code, actCount, pos=begin, endpos=end)
			replaced += foundCount
		self.__shiftAndClearLineJoins(shifts)
		self.recalcCode()

		return replaced


	def insert(self, pos, repl):
		self.replaceRange(pos, pos, repl)


	# Tries to scope to the body of the given class or classes if name is a regex
	def tryScopeToClassBody(self, name, scopes=None, *, skipBlocks=True):
		return self.tryScopeToClassStructBody("class", name, scopes, skipBlocks=skipBlocks)


	# Tries to scope to the body of the given struct or structs if name is a regex
	def tryScopeToStructBody(self, name, scopes=None, *, skipBlocks=True):
		return self.tryScopeToClassStructBody("struct", name, scopes, skipBlocks=skipBlocks)

	
	# Tries to scope to the body of the given class or struct or many if name is a regex
	def tryScopeToClassStructBody(self, kind, name, scopes=None, *, skipBlocks=True):
		assert kind in ["class", "struct", None]
		if not kind: kind = "class|struct"

		if scopes:
			oldScopes = self.__scopes
			self.setScopes(scopes)

		prefixRe = f"\\b{kind}\\s+{name}\\b"

		if skipBlocks:
			prefixPat = SourceFile.makeSkipBlocksPat(prefixRe)
			find = self.__findPatUnscoped_SkipBlocks
		else:
			prefixPat = regex.compile(prefixRe)
			find = self.__findPatUnscoped

		foundScopes = []

		pos = 0
		for scope in self.__scopes:
			begin = scope[0]
			end   = scope[1]
			#if tagged := len(scope) == 3:
			#	tag = scopes[2]
			if begin is not None and pos < begin:
				pos = begin
			while (end is None or pos < end) and (imres := find(prefixPat, pos, end)):
				match Syntax.parseClassStructPrefix(kind, name, self.__code, imres.start()):
					case (foundkind, foundname, pos): pass
					case None:
						pos = imres.end()
						continue
				blockEnd = self.__blockEnds[pos]
				foundScopes.append((pos + 1, blockEnd, (foundkind, foundname)))
				pos = blockEnd + 1

		if foundScopes:
			self.__scopes = foundScopes
			return True
		else:
			if scopes: self.__scopes = oldScopes
			return False
		

	# Tries to scope to all bodis of the namespace nsname or namespaces if given a regex
	def tryScopeToNamespaceBody(self, nsname, scopes=None, *, skipBlocks=True):
		return self.tryScopeToBlocksByPrefix(Syntax.makeNamespacePrefixRe(f"(?:{nsname})"), scopes, 
									         tagFunc=lambda mres, _: mres.group("name"), skipBlocks=skipBlocks)
	

	def tryScopeToBlocksByPrefix(self, prefixRe, scopes=None, *, tagFunc=lambda _, __: None, skipBlocks=True):
		if scopes:
			oldScopes = self.__scopes
			self.setScopes(scopes)

		if skipBlocks:
			prefixPat = SourceFile.makeSkipBlocksPat(prefixRe)
			find = self.__findPatUnscoped_SkipBlocks
		else:
			prefixPat = regex.compile(prefixRe)
			find = self.__findPatUnscoped

		foundScopes = []

		pos = 0
		for scope in self.__scopes:
			begin = scope[0]
			end   = scope[1]
			#if tagged := len(scope) == 3:
			#	tag = scopes[2]
			if begin is not None and pos < begin: 
				pos = begin
			while (end is None or pos < end) and (mres := find(prefixPat, pos, end)):
				pos = mres.end()
				blockEnd = self.__blockEnds[pos - 1]
				foundScopes.append( (pos, blockEnd, tagFunc(mres, scope)) )
				pos = blockEnd + 1

		if foundScopes:
			self.__scopes = foundScopes
			return True
		else:
			if scopes: self.__scopes = oldScopes
			return False


	def insertSPrefixInBlockMatch(self, blockBegin, *, skipComments=False):
		blockBegin = self._intPos(blockBegin)
		assert blockBegin in self.__blockEnds, "No block in the given position"
		blockEnd   = self.__blockEnds[blockBegin]
		imres = self.__matchPatUnscoped(_blockStartSkipComPat if skipComments else _blockStartPat, 
								        blockBegin + 1, blockEnd + 1)
		if imres.group("ind"):
			suffix = "\r\n" + imres.captures("ind")[0]
		elif imres.group("preproc"):
			suffix = "\r\n" + self.indent
		elif imres.start("ins") != blockEnd or imres.group("ts"):
			suffix = " "
		else:
			suffix = ""
		return (sm.SourceRangeMatch(self, (imres.start("ins"), imres.start("ins")), intRanges=True), suffix)


	def insertSPrefixInBlock(self, blockBegin, prefix, *, skipComments=False):
		assert "\r\n" not in prefix, "Multiline prefix"
		(mres, prefixEnd) = self.insertSPrefixInBlockMatch(blockBegin, skipComments=skipComments)
		self.replaceMatch(mres, prefix + prefixEnd)

		#beginBlockLn = self._intLineNo(blockBegin)
		#endBlockLn   = self._intLineNo(blockEnd)

		#if beginBlockLn == endBlockLn and prefix.count("\r\n") == 0:
		#	imres = self.__matchPatUnscoped(_spacePat, blockBegin + 1)
		#	replMatch = sm.SourceRangeMatch(self, (imres.end(), imres.end()), intRanges=True)
		#	self.replaceMatch(replMatch, prefix + " ")

		#else:
		#	imres = self.__matchPatUnscoped(_block0Pat, blockBegin)
		#	replMatch = sm.SourceRangeMatch(self, (imres.start(2), blockEnd), intRanges=True)
		#	indent = imres.group(1)
		#	newblock = Syntax.expandBlock(self.__code[blockBegin:blockEnd+1])
		#	newblock = Syntax.indent(imres.group(1),
		#								"{\r\n" 
		#								f"{self.indent}{prefix}\r\n"
		#								f"{newblock[3:]}")
		#	self.replaceMatch(replMatch, imres.group(1) + newblock)


	def _blockExtension(self, ibegin, iend):
		if iend   is None: return len(self.__code)
		if ibegin is None: ibegin = 0
		ext = iend
		i = ibegin
		while i < iend:
			if self.__code[i] == '{':
				if range := self.getClipRangeInt(i):
					i = range[1]
				else:
					blockEnd = self.__blockEnds[i]
					ext = max(ext, blockEnd)
					i = blockEnd
			else:
				i += 1
		return ext


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

		if begins != []:
			with open("dump.cpp", "w", encoding="utf-8", newline="") as f:
				f.write(self.__code)

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


	def checkSkipBlocksPat(pat):
		return pat.pattern.endswith(r"|(?P<__cppcr_sbo>\{)")
