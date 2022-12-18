from .utils import *
from .syntax import *
from . import sourcematch as sm
import numpy


class SourceFile:
	__filename   = None
	__code       = None
	__lineJoins  = None
	__clipRanges = None
	__lineEnds   = None
	__blocksEnds = None
	__scopes     = None
	

	def __init__(self, filename=None):
		if filename: 
			self.load(filename)


	def load(self, filename, encoding="utf-8"):
		self.__filename = filename
		with open(filename, "r", encoding=encoding, newline="") as f:
			self.__code = f.read()
			self.__joinLines()
			self.resetScopes()
			self.__makeClipRangesAndLineEnds()
			self.__makeBlockEnds()


	def save(self, encoding="utf-8"):
		assert self.isLoaded(), "No loaded file."
		self.saveAs(self.__filename, encoding)


	def saveAs(self, filename, encoding="utf-8"):
		with open(filename, "w", encoding=encoding, newline="") as f:
			f.write(self.__code)
			f.flush()
			self.__filename = filename


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
	def __findAllGen(self, pat, excludeClips=True):
		for (begin, end) in self.__scopes:
			if type(pat) is not regex.Pattern:
				pat = regex.compile(pat)
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
					begin = self.__blocksEnds[mres.start()]
				elif not excludeClips or not self.isClipped(mres.start()):
					begin = mres.end()
					yield mres
				

	def __findPatUnscoped(self, pat, begin, end=None, excludeClips=True):
		while mres := pat.search(self.__code, begin, end):
			if not excludeClips or not self.isClipped(mres.start()):
				return mres
			else:
				begin = mres.end()
			
				
	def __findReUnscoped_SkipBlocks(self, re, begin, end=None, excludeClips=True):
		pat = regex.compile(re + r"|\{")
		while mres := pat.search(self.__code, begin, end):
			if excludeClips and self.isClipped(mres.start()):
				begin = mres.end()
			elif mres.group() == "{":
				begin = self.__blocksEnds[mres.start()]
			else:
				return mres


	def __find(self, pat, excludeClips=True):
		return next(self.__findAllGen(pat, excludeClips), None)
	

	def __find_SkipBlocks(self, pat, excludeClips=True):
		return next(self.__findAllGen_SB(pat, excludeClips), None)


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
		while mres := next(gen, None):
			yield sm.SourceMatch(self, mres)
			

	# result - generator
	def findAllGen_SkipBlocks(self, pat, *, excludeClips=True):
		gen = self.__findAllGen_SkipBlocks(pat, excludeClips)
		while mres := next(gen, None):
			yield sm.SourceMatch(self, mres)


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
		def onMatch(m):
			joins.append(m.start() - 3*len(joins))
			return ""
		self.__code = regex.sub(r"\\\r\n", onMatch, self.__code)
		self.__lineJoins = numpy.array(joins)


	def _lnJoinsBefore(self, pos):
		return numpy.searchsorted(self.__lineJoins, pos, 'right')


	def _orgPos(self, pos):
		return pos + 3*self._lnJoinsBefore(pos)


	def _intLocation(self, pos):
		ln = numpy.searchsorted(self.__lineEnds, pos, 'right')
		col = pos - self.__lineEnds[ln-1] if ln > 0 else pos
		return (ln, col)
	

	def _intOrgLocation(self, pos):
		ln = numpy.searchsorted(self.__lineEnds, pos, 'right')
		lnStart = self.__lineEnds[ln-1] if ln > 0 else 0
		if joinsBefore := self._lnJoinsBefore(pos):
			lastJoin = self.__lineJoins[joinsBefore-1]
			lnStart = max(lnStart, lastJoin)
		return (ln + joinsBefore, pos - lnStart)
