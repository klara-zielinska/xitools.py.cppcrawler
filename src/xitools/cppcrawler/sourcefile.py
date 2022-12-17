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
	__scopeBegin = None
	__scopeEnd   = None
	

	def __init__(self, filename=None):
		if filename: 
			self.load(filename)


	def load(self, filename, encoding="utf-8"):
		self.__filename = filename
		with open(filename, "r", encoding=encoding, newline="") as f:
			self.__code = f.read()
			self.__joinLines()
			self.resetScope()
			self.__makeClipRangesAndLineEnds()
			self.__makeBlockEnds()


	def resetScope(self):
		self.__scopeBegin = None
		self.__scopeEnd   = None

	def scope(self):
		return (self.__scopeBegin, self.__scopeEnd)

	def setScope(self, begin, end):
		self.__scopeBegin = begin
		self.__scopeEnd   = end


	def isClipped(self, pos):
		for (start, end, _) in self.__clipRanges:
			if start > pos:
				return False
			elif end > pos:
				return True
		return False
	

	# result - generator
	def __findAllGen(self, pat, begin=None, end=None, excludeClips=True):
		if begin is None: begin = self.__scopeBegin
		if end   is None: end   = self.__scopeEnd
		if type(pat) is not regex.Pattern:
			pat = regex.compile(pat)
		for mres in pat.finditer(self.__code, begin, end):
			if not excludeClips or not self.isClipped(mres.start()):
				yield mres
				

	# result - generator
	def __findAllGen_SkipBlocks(self, pat, begin=None, end=None, excludeClips=True):
		if begin is None: begin = self.__scopeBegin
		if end   is None: end   = self.__scopeEnd
		if pat is regex.Pattern: 
			pat = pat.pattern
		pat += r"|\{"
		pat = regex.compile(pat)
		while mres := pat.search(self.__code, begin, end):
			if mres.group(0) == "{":
				begin = self.__blocksEnds[mres.start()]
			elif not excludeClips or not self.isClipped(mres.start()):
				begin = mres.end()
				yield mres
				

	def __find(self, pat, begin=None, end=None, excludeClips=True):
		return next(self.__findAllGen(pat, begin, end, excludeClips), None)
	

	def __find_SkipBlocks(self, pat, begin=None, end=None, excludeClips=True):
		return next(self.__findAllGen_SB(pat, begin, end, excludeClips), None)


	def find(self, pat, begin=None, end=None, *, excludeClips=True):
		if mres := self.__find(pat, begin, end, excludeClips):
			return sm.SourceMatch(self, mres)
		else:
			return None
		

	def find_SkipBlocks(self, pat, begin=None, end=None, *, excludeClips=True):
		if mres := next(self.__find_SkipBlocks(pat, begin, end, excludeClips), None):
			return sm.SourceMatch(self, mres)
		else:
			return None
		

	# result - generator
	def findAllGen(self, pat, begin=None, end=None, *, excludeClips=True):
		gen = self.__findAllGen(pat, begin, end, excludeClips)
		while mres := next(gen, None):
			yield sm.SourceMatch(self, mres)
			

	# result - generator
	def findAllGen_SkipBlocks(self, pat, begin=None, end=None, *, excludeClips=True):
		gen = self.__findAllGen_SkipBlocks(pat, begin, end, excludeClips)
		while mres := next(gen, None):
			yield sm.SourceMatch(self, mres)


	# heuristic selection of the body of the given class
	# selection = scoping to
	# return: the position of the class definition or -1 in none
	def tryScopeToClassBody(self, cname, scope=None):
		if scope:
			oldScope = self.scope() 
			self.setScope(*scope)

		if mres := self.__find(Syntax.makeClassPrefixRe(cname)):
			begin = mres.end()
			self.setScope(begin, self.__blocksEnds[begin - 1])
			return self._orgPos(mres.start())
		else:
			if scope: self.setScope(*oldScope)
			return -1
	

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


	def __makeBlockEnds(self):
		self.__blocksEnds = {}
		pos = 0
		begins = []
		while mres := self.__find(r"[\{}]", pos):
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

