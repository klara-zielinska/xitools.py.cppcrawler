from .utils import *
from .syntax import *
from .syntax import ___
from . import sourcematch as sm
import bisect
import shutil
import errno
import os


_openBlockPat   = regex.compile("{")
_clipBeginPat   = regex.compile(r"['\"]|//|/\*|\r\n")
_endCharPat     = regex.compile(r"'|\r\n|$")
_endStrPat      = regex.compile(r'"|\r\n|$')
_endComment1Pat = regex.compile(r'\r\n|$')
_endCommentNOrNlPat = regex.compile(r'\*/|\r\n|$')

_blockStartPat = regex.compile(
		r"\s*"
		r"\r\n(?P<ins>)[ \t]*#.*"
		r"\s*\r\n(?P<ind>[ \t]*)(?P<del>\S)"
	r"|"
		r"\s*"
		r"\r\n(?P<ins>)(?P<ind>[ \t]*)(?P<del>\S)"
	r"|"
		r"(?P<ind1>[ \t]*)(?P<ins0>)(?P<del1>\S).*"
		r"(?:\s*(?<=\r\n)(?P<ind2>[ \t]*)\S)?")



## Class for storing C++ source files.
#  @anchor SourceFile
#
# Currently only Windows files are supported.
#
# The line break sequences `\<new line>` are removed from the code on loading, however their positions are stored.
#
# The code positions taken and returned by public methods are by default positions in the original code. Respectively, 
# positions operated by internal methods (names starting with `_`) are the internal positions.
# 
# Some public methods accept the int switch that makes them operate on internal positions when set `True`.
class SourceFile:

	## Default indentation used in code generation.
	defaultIndent  = " "*4

	__filepath     = None
	__code         = None
	__lineJoins    = None
	__lineJoinsOrg = None
	__clipRanges   = None
	__lineEnds     = None
	__blockEnds    = None
	__scopes       = None
	

	##
	# @param filepath  If passed, the file is automatically loaded. See SourceFile.load.
	# @param encoding  The encoding.
	def __init__(self, filepath=None, encoding="utf-8"):
		if filepath:
			self.load(filepath, encoding)
			
        
	def __str__(self):
		return (f"<xitools.cppcrawler.SourceFile object; "
			    f"filepath='{self.filepath()}'>")


	def __repr__(self):
		return (f"<xitools.cppcrawler.SourceFile object at {hex(id(self))}; "
			    f"filepath='{self.filepath()}'>")

	## The absolute file path.
	def filepath(self):
		return self.__filepath


	## Given an internal position return the original position.
	def orgPos(self, pos):
		if pos is None:
			return None
		else:
			return pos + 3*self._lineJoinsBefore(pos)
	
		
	## Given an original position return the internal position.
	def intPos(self, pos):
		if pos is None:
			return None
		else:
			n = self._lineJoinsOrgBefore(pos)
			correct = 0
			if n > 0:
				space = pos - self.__lineJoinsOrg[n - 1]
				correct = 3 - min(space, 3)
			return pos - 3*n + correct
    
	
	## Given an internal scope, possibly tagged, returns the scope with original positions.
	def orgScope(self, scope):
		return (self.orgPos(scope[0]), self.orgPos(scope[1])) + (() if len(scope) == 2 else (scope[2],))


	## Given a scope with original positions, possibly tagged, returns the internal scope.
	def intScope(self, scope):
		return (self.intPos(scope[0]), self.intPos(scope[1])) + (() if len(scope) == 2 else (scope[2],))
	

	## Given a position returns the pair: internal line number, character position in the line.
	def intLocation(self, pos, *, int=False):
		if not int: pos = self.intPos(pos)
		ln = bisect.bisect_right(self.__lineEnds, pos) + 1
		lnStart = self.__lineEnds[ln-2] if ln > 1 else 0
		return (ln, pos - lnStart + 1)
	

	## Given a position returns the pair: original line number, character position in the line.
	def orgLocation(self, pos, *, int=False):
		if not int: pos = self.intPos(pos)
		ln = bisect.bisect_right(self.__lineEnds, pos) + 1
		lnStart = self.__lineEnds[ln-2] if ln > 1 else 0
		if joinsBefore := self._lineJoinsBefore(pos):
			ln += joinsBefore
			lastJoin = self.__lineJoins[joinsBefore-1]
			lnStart  = max(lnStart, lastJoin)
		return (ln, pos - lnStart + 1)


	## Returns a piece of the internal code.
	# 
	# If `start` = `end` = `None`, the returned string is not copied out.
	def intCode(self, start=None, end=None, *, int=False):
		if not int:
			start = self.intPos(start)
			end   = self.intPos(end)
		return self.__code[start:end]


	## Returns a piece of the original code. (Low performance)
	#
	# The method is inefficient if file contains `\<new line>` sequences. Use SourceFile.intCode instead.
	def orgCode(self, start=None, end=None, *, int=False):
		if len(self.__lineJoins) == 0:
			return self.__code[start:end]

		if not int:
			start = self.intPos(start)
			end   = self.intPos(end)
			
		if start is None: start = 0
		if end   is None: end   = len(self.__code)

		chunkBegin = start
		chunks = []
		for pos in self.__lineJoins[self._lineJoinsBefore(start):self._lineJoinsBefore(end)]:
			chunks.append(self.__code[chunkBegin:pos])
			chunkBegin = pos
		chunks.append(self.__code[chunkBegin:end])
		return "\\\r\n".join(chunks)


	## Abbreviation that calls SourceFile.intLocation and returns the first element.
	def intLineNo(self, pos, *, int=False):
		return self.intLocation(pos, int=int)[0]


	## Abbreviation that calls SourceFile.orgLocation and returns the first element.
	def orgLineNo(self, pos, *, int=False):
		return self.orgLocation(pos, int=int)[0]


	## Returns the block end position (any `{ ... }`).
	def blockEnd(self, begin, *, int=False):
		if int:
			return self.__blockEnds[begin]
		else:
			return self.orgPos(self.__blockEnds[self.intPos(begin) ])
		

	def _intScopes(self):
		return self.__scopes


	## Returns a copy of the current search scopes. The scopes are triples `(begin, end, tag)`.
	def scopes(self):
		return [ (self.orgPos(begin), self.orgPos(end), tag) for (begin, end, tag) in self.__scopes ]


	## Sets the search scope to the entire file.
	def resetScopes(self):
		self.__scopes = [(None, None, None)]

		
	## Set a single search scope.
	def setScope(self, begin, end, tag=None):
		self.__scopes = [(self.intPos(begin), self.intPos(end), tag)]


	## Set search scopes.
	def setScopes(self, scopes):
		if type(scopes) is tuple:
			scopes = [scopes]
		assert type(scopes) is list
		self.__scopes = [ (self.intPos(scope[0]), self.intPos(scope[1]), scope[2] if len(scope) == 3 else None)
						  for scope in scopes ]
		self.__scopes.sort()

		
	def _isClipped(self, pos):
		for (start, end, _) in self.__clipRanges:
			if start > pos:
				return False
			elif end > pos:
				return True
		return False


	## Checks if a position is in a clipped range -- a comment, a string literal or a char literal. 
	def isClipped(self, pos, *, int=False):
		if not int: pos = self.intPos(pos)
		return self._isClipped(pos)


	def _getClipRange(self, pos):
		for range in self.__clipRanges:
			(start, end, tag) = range
			if start > pos:
				return None
			elif end > pos:
				return range
		return None
	
	
	## Returns the first clipped range containing the position, that is, a comment, a string literal or a char literal. 
	def getClipRange(self, pos, *, int=False):
		if int: 
			return self._getClipRange(pos)
		else:
			match self._getClipRange(self.intPos(pos)):
				case (start, end, tag): return (self.orgPos(start), self.orgPos(end), tag)
				case None:              return None


	## Given a position returns the start position of the line.
	#
	# The lines are evaluated after `\<new line>` removal (e.g., for `"int\\\r\nx;"` and `pos=6` the result is `0`)
	def lineStart(self, pos):
		ln = self.intLineNo(self.intPos(pos))
		return self.orgPos(0 if ln == 1 else self.__lineEnds[ln - 2])


	## Returns a shallow copy.
	def copy(self):
		cp = SourceFile()
		cp.__filepath   = self.__filepath
		cp.__encoding   = self.__encoding
		cp.__code       = self.__code
		cp.__lineJoins  = self.__lineJoins.copy()
		cp.__lineJoinsOrg = self.__lineJoinsOrg.copy()
		cp.__clipRanges = self.__clipRanges.copy()
		cp.__lineEnds   = self.__lineEnds.copy()
		cp.__blockEnds  = self.__blockEnds.copy()
		cp.__scopes     = self.__scopes.copy()
		return cp

	
	## Loads a source file.
	def load(self, filepath, encoding="utf-8-sig"):
		self.__filepath = os.path.abspath(filepath)
		self.__encoding = encoding
		with open(self.__filepath, "r", encoding=encoding, newline="") as f:
			self.__code = f.read()
			self.__joinLines()
			self.resetScopes()
			self._recalcCode()


	## Saves the source. See SourceFile.saveAs.
	def save(self, encoding=None, *, backupDir=None, force=False):
		self.saveAs(self.__filepath, encoding, backupDir=backupDir, force=force)


	## Saves the source in a given location.
	#
	# The sequences `\<new line>` are reincorporated in the saved file.
	#
	# @param filepath   Path to save.
	# @param encoding   If `None`, the encoding passed when on loading is used (see SourceFile.load).
	# @param backupDir  If set and the file already exists, a backup of it will be saved in this location.
	# @param force      If the file already exists, this flag confirms if it should be overwritten.
	def saveAs(self, filepath, encoding=None, *, backupDir=None, force=False):
		assert self.__filepath, "No file name."
		if not encoding: encoding = self.__encoding
		if os.path.exists(filepath) and not force:
			raise FileExistsError(errno.EEXIST, "File exists, use force to override", filepath)
		if backupDir:
			backupName = os.path.join(backupDir, os.path.basename(filepath))
			if os.path.exists(backupName): 
				raise FileExistsError(errno.EEXIST, "Backup file already exists", backupName)
			shutil.copy2(filepath, backupName)
		with open(filepath, "w", encoding=encoding, newline="") as f:
			f.write(self.orgCode())
			f.flush()
			self.__filepath = filepath


	## Finds the beginning of the first block behind the given.
	def findFirstBlock(self, pos):
		if mres := self._findPatUnscoped(_openBlockPat, self.intPos(pos)):
			return (self.orgPos(mres.start()), self.orgPos(self.__blockEnds[mres.start()] + 1))
		else:
			return None


	## Creates a `regex.Pattern` to be use in methods that can skip blocks.
	def makeSkipBlocksPat(re):
		return regex.compile(re + r"|(?P<__cppcr_sbo>\{)")


	## Checks if a `regex.Pattern` is properly formed to be used in methods that can skip blocks.
	def checkSkipBlocksPat(pat):
		return pat.pattern.endswith(r"|(?P<__cppcr_sbo>\{)")
	
		
	def _findAllPat_Unscoped(self, pat, start, end, excludeClips=True):
		while mres := pat.search(self.__code, start, end):
			if excludeClips and (range := self._getClipRange(mres.start())):
				start = range[1]
			else:
				start = mres.end()
				yield mres
	
				
	def _findAllPat_Unscoped_SkipBlocks(self, pat, start, end, excludeClips=True):
		while mres := pat.search(self.__code, start, end):
			if mres.group("__cppcr_sbo"):
				if self._isClipped(mres.start()):
					start = mres.end()
				else:
					start = self.__blockEnds[mres.start()]
			else:
				if excludeClips and (range := self._getClipRange(mres.start())):
					start = range[1]
				else:
					start = self._blockExtension(start, mres.end())
					yield mres

					
	def _findAllPat(self, pat, excludeClips=True, scopeTag=False):
		if scopeTag: 
			def wrapRes(mres, stag): return (mres, stag)
		else:       
			def wrapRes(mres, stag): return mres

		for (begin, end, stag) in self.__scopes:
			while mres := pat.search(self.__code, begin, end):
				if excludeClips and (range := self._getClipRange(mres.start())):
					begin = range[1]
				else:
					begin = mres.end()
					yield wrapRes(mres, stag)

					
	def _findAllPat_SkipBlocks(self, pat, excludeClips=True, scopeTag=False):
		if scopeTag: 
			def wrapRes(mres, stag): return (mres, stag)
		else:       
			def wrapRes(mres, stag): return mres

		for (begin, end, stag) in self.__scopes:
			while mres := pat.search(self.__code, begin, end):
				if mres.group("__cppcr_sbo"):
					if self._isClipped(mres.start()):
						begin = mres.end()
					else:
						begin = self.__blockEnds[mres.start()]
				else:
					if excludeClips and (range := self._getClipRange(mres.start())):
						begin = range[1]
					else:
						begin = self._blockExtension(begin, mres.end())
						yield wrapRes(mres, stag)

						
	def _matchPatUnscoped(self, pat, start, end=None, excludeClips=True):
		if excludeClips and self._getClipRange(start):
			return None
		else:
			return pat.match(self.__code, start, end)

		
	def _fullmatchPatUnscoped(self, pat, start, end, excludeClips=True):
		if excludeClips and self._getClipRange(start):
			return None
		else:
			return pat.fullmatch(self.__code, start, end)


	def _findPatUnscoped(self, pat, start, end=None, excludeClips=True):
		while mres := pat.search(self.__code, start, end):
			if excludeClips and (range := self._getClipRange(mres.start())):
				start = range[1]
			else:
				return mres

	##			
	# @param pat  Has to be prepared with SourceFile.makeSkipBlocksPat or be equivalent.
	def _findPatUnscoped_SkipBlocks(self, pat, start, end=None, excludeClips=True):
		while mres := pat.search(self.__code, start, end):
			if mres.group("__cppcr_sbo"):
				if self._isClipped(mres.start()):
					start = mres.end()
				else:
					start = self.__blockEnds[mres.start()]
			else:
				if excludeClips and (range := self._getClipRange(mres.start())):
					start = range[1]
				else:
					return mres


	def _findPat(self, pat, excludeClips=True, scopeTag=False):
		return next(self._findAllPat(pat, excludeClips, scopeTag), None)
	

	def _findPat_SkipBlocks(self, pat, excludeClips=True, scopeTag=False):
		return next(self._findAllPat_SkipBlocks(pat, excludeClips, scopeTag), None)
		

	## Finds the first occurrence of a pattern in the search scopes.
	#
	# @param pat  Regular expression -- can be from re or from its extension `regex` module -- or a regular expression 
	#		      compiled with `regex.compile`. If `skipBlocks=True`, it has to be prepared with 
	#             SourceFile.makeSkipBlocksPat or be equivalent.
	# @param skipBlocks  If `True`, excludes blocks (any `{ ... }`) that start in the examined scopes from the search.
	# @param scopeTag      If `True`, a pair `(`@ref SourceRegexMatch `, tag)` is returned, where tag is the tag of 
	#                      the scope where the occurrence was found.
	# @param excludeClips  If `True`, clipped ranges are excluded from the search (see SourceFile.isClipped).
	# @return     Depending on scopeTag either SourceRegexMatch, or `(`@ref SourceRegexMatch `, tag)`, or `None`.
	#
	# @remark  By exclusion we mean that a match cannot start in a given range, however it can start before and 
	#          overlap it.
	def find(self, pat, *, skipBlocks=False, scopeTag=False, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = SourceFile.makeSkipBlocksPat(pat) if skipBlocks else regex.compile(pat)
		else:
			assert not skipBlocks or SourceFile.checkSkipBlocksPat(pat)

		if skipBlocks: timres = self._findPat_SkipBlocks(pat, excludeClips, scopeTag)
		else:          timres = self._findPat(pat, excludeClips, scopeTag)
		if not timres: return None
		elif scopeTag:
			mres = sm.SourceRegexMatch(self, timres[0])
			return (mres, timres[1])
		else:       
			return sm.SourceRegexMatch(self, timres)
			
		
	## Finds all occurrences of a pattern in the search scopes.
	#
	# Returns a generator. See SourceFile.find for more details.
	def findAll(self, pat, *, skipBlocks=False, scopeTag=False, excludeClips=True):
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
		
		if skipBlocks: gen = self._findAllPat_SkipBlocks(pat, excludeClips, scopeTag)
		else:          gen = self._findAllPat(pat, excludeClips, scopeTag)
		while tmres := next(gen, None):
			yield wrapRes(tmres)
	

	## Matches the source against a regular expression ignoring the search scopes.
	#
	# The matched range is specified with the `start`, `end` parameters. See SourceFile.find for more details.
	def matchUnscoped(self, pat, start, end=None, *, excludeClips=True):
		if start is None: start = 0
		if type(pat) is not regex.Pattern:
			pat = regex.compile(pat)
		if start is not None: start = self.intPos(start)
		if end   is not None: end   = self.intPos(end)
		mres = self._matchPatUnscoped(pat, start, end, excludeClips)
		return sm.SourceRegexMatch(self, mres) if mres else None
	

	## Analogous to SourceFile.matchUnscoped, but performs a full match.
	def fullmatchUnscoped(self, pat, start, end, *, excludeClips=True):
		if start is None: start = 0
		if type(pat) is not regex.Pattern:
			pat = regex.compile(pat)
		if start is not None: start = self.intPos(start)
		if end   is not None: end   = self.intPos(end)
		mres = self._fullmatchPatUnscoped(pat, start, end, excludeClips)
		return sm.SourceRegexMatch(self, mres) if mres else None


	## Finds the first occurrence of a pattern ignoring the search scopes.
	#
	# The searched range is specified with the `start`, `end` parameters. See SourceFile.find for more details.
	def findUnscoped(self, pat, start=None, end=None, *, skipBlocks=False, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = SourceFile.makeSkipBlocksPat(pat) if skipBlocks else regex.compile(pat)
		else:
			assert not skipBlocks or SourceFile.checkSkipBlocksPat(pat)
		if start is not None: start = self.intPos(start)
		if end   is not None: end   = self.intPos(end)

		if skipBlocks: mres = self._findPatUnscoped_SkipBlocks(pat, start, end, excludeClips)
		else:          mres = self._findPatUnscoped(pat, start, end, excludeClips)
		return sm.SourceRegexMatch(self, mres) if mres else None
	
			
	## Finds all occurrences of a pattern ignoring the search scopes.
	#
	# The searched range is specified with the `start`, `end` parameters. See SourceFile.find for more details.
	def findAllUnscoped(self, pat, start=None, end=None, *, skipBlocks=False, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = SourceFile.makeSkipBlocksPat(pat) if skipBlocks else regex.compile(pat)
		else:
			assert not skipBlocks or SourceFile.checkSkipBlocksPat(pat)
		if start is not None: start = self.intPos(start)
		if end   is not None: end   = self.intPos(end)
		srcMatchCopy = self.copy()
		
		if skipBlocks: gen = self._findAllPat_Unscoped_SkipBlocks(pat, start, end, excludeClips)
		else:		   gen = self._findAllPat_Unscoped(pat, start, end, excludeClips)
		while mres := next(gen, None):
			yield sm.SourceRegexMatch(srcMatchCopy, mres, copySource=False)


	## Replaces matches in the source.
	#
	# @param tmatches  List of @ref SourceMatch or pairs `(` @ref SourceMatch `, tag)` -- `tag` can be anything.
	#                  The matches cannot overlap -- the result unspecified.
	# @param repl      Replacement - a string or a function accepting either a @ref SourceMatch or 
	#                  `(` @ref SourceMatch `, tag)`, depending on the type of tmatches, and returning a string. The 
	#                  string cannot contain sequences `\<new line>`.
	# @param sorted    If `True`, tmatches are assumed to be sorted with respect to the position. Otherwise tmatches 
	#                  are copied and sorted.
	def replaceMatches(self, tmatches, repl, *, sorted=False):
		if not tmatches:
			return
		if not sorted:
			tmatches = tmatches.copy()
			tmatches.sort()
		if type(repl) is str:
			_repl = repl
			repl = lambda _: _repl
		if type(tmatches[0]) == tuple: # is tagged
			def getMres(tm): return tm[0]
		else:
			def getMres(m): return m
		shifts = []
		newCode = []
		chunkBegin = 0
		for tm in tmatches:
			mres = getMres(tm)
			newCode.append(self.__code[chunkBegin:mres.intStart()])
			replStr = repl(tm)
			assert "\\\r\n" not in replStr
			newCode.append(replStr)
			chunkBegin = mres.intEnd()
			shifts.append((mres.intStart(), mres.intEnd(), len(replStr) - len(mres.group(0))))
		newCode.append(self.__code[chunkBegin:])
		self.__code = "".join(newCode)
		self.__shiftAndClearLineJoins(shifts)
		self._recalcCode()


	## Abbreviation that calls SourceFile.replaceMatches with a single match.
	def replaceMatch(self, match, repl):
		self.replaceMatches([match], repl)


	## Abbreviation that creates a @ref SourceRangeMatch and calls SourceFile.replaceMatch with it.
	def replaceRange(self, start, end, repl):
		self.replaceMatch(sm.SourceRangeMatch(self, (start, end)), repl)


	## Replace occurrences of a pattern in the source.
	#
	# @param pat    Regular expression -- can be from re or from its extension `regex` module -- or a regular 
	#		        expression compiled with `regex.compile`. If `skipBlocks=True`, it has to be prepared with 
	#               SourceFile.makeSkipBlocksPat or be equivalent.
	# @param repl   Replacement -- a string or a function taking @ref SourceMatch and returning a string. The string 
	#               cannot contain sequences `\<new line>`. Currently there is no support for tags.
	# @param count  Limit of performed replacements -- `0` means no limit.
	# @param excludeClips  If `True`, clipped ranges are excluded from the search (see SourceFile.isClipped).
	# @return              The number of performed replacements.
	def replace(self, pat, repl, count=0, *, excludeClips=True):
		if type(pat) is not regex.Pattern:
			pat = regex.compile(pat)
		if type(repl) is str:
			_repl = repl
			repl = lambda _: _repl
		shifts = []
		replaced = 0

		def inRepl(mres):
			nonlocal replaced
			if excludeClips and self._isClipped(mres.start()) or count != 0 and replaced == count:
				return mres.group(0)
			else:
				repStr = repl(mres)
				assert "\\\r\n" not in repStr
				shifts.append( (mres.start(), mres.end(), len(repStr) - len(mres.group(0))) )
				replaced += 1
				return repStr

		for (begin, end, _) in self.__scopes:
			self.__code = pat.sub(inRepl, self.__code, pos=begin, endpos=end)
			if count != 0 and replaced == count: break
		self.__shiftAndClearLineJoins(shifts)
		self._recalcCode()

		return replaced


	## Inserts code in the given position -- abbreviation of SourceFile.replaceRange applied to `pos`, `pos`.
	def insert(self, pos, code):
		self.replaceRange(pos, pos, code)

	
	## Tries to set the search scope to the body of a `class`, `struct`, `union` or a collection of either.
	#
	# If the method succeed, the tags of the new scopes are tuples `(kind, name)` or `(kind, name, tag)`, where 
	# `kind` is either `"class"`, "struct" or `"union"`, `name` is the name and `tag` is the tag of the scope that 
	# was searched.
	#
	# @param kind    Either `"class"`, `"struct"` or `"union"`, or any combination of these separated with `|`; or 
	#                `"*"` -- any.
	# @param name    String or regular expression.
	# @param scopes  If present, the search is performed in the given *<scope>* collection, where *<scope>* is 
    #                a tuple `(begin, end)` or `(begin, end, tag)`, `begin`, `end` are positions in the code 
	#                and `tag` is anything.
	# @param skipBlocks  If `True`, excludes blocks (any `{ ... }`) that start in the examined scopes from the search.
	# @param scopeTag    If `True`, the new scopes contain the tag part.
	# @return  `True` if the scopes were set, otherwise `False`.
	def tryScopeToClassBody(self, kind, name, scopes=None, *, skipBlocks=True, scopeTag=False):
		assert kind == "*" or not [True for k in kind.split("|") if k not in ["class", "struct", "union"]]
		if kind == "*": kind = "class|struct|union"

		if scopes:
			oldScopes = self.__scopes
			self.setScopes(scopes)

		prefixRe = f"\\b(?:{kind})\\s+{name}\\b"

		if skipBlocks:
			prefixPat = SourceFile.makeSkipBlocksPat(prefixRe)
			find = self._findPatUnscoped_SkipBlocks
		else:
			prefixPat = regex.compile(prefixRe)
			find = self._findPatUnscoped

		foundScopes = []

		pos = 0
		for scope in self.__scopes:
			(begin, end, stag) = scope
			if begin is not None and pos < begin:
				pos = begin
			while (end is None or pos < end) and (imres := find(prefixPat, pos, end)):
				match Syntax.parseClassPrefix(self.__code, imres.start()):
					case (foundkind, foundname, _, _, pos):
						if self.__code[pos] != "{": continue
					case None:
						pos = imres.end()
						continue
					case _: # pragma: no cover
						assert False
				blockEnd = self.__blockEnds[pos]
				foundScopes.append((pos + 1, blockEnd, (foundkind, foundname) + ((stag,) if scopeTag else ()) ))
				pos = blockEnd + 1

		if foundScopes:
			self.__scopes = foundScopes
			return True
		else:
			if scopes: self.__scopes = oldScopes
			return False
		

	## Like SourceFile.tryScopeToClassStructBody, but scopes to namespaces.
	def tryScopeToNamespaceBody(self, name, scopes=None, *, skipBlocks=True, scopeTag=False):
		if scopeTag:
			def tagFunc(mres, scope): return (mres.group("name"), scope[2])
		else:
			def tagFunc(mres, scope): return mres.group("name")
		return self.tryScopeToBlockByPrefix(f"namespace{___}(?P<name>{name}){___}", scopes, 
									         tagFunc=tagFunc, skipBlocks=skipBlocks)
	

	## Tries to set the search scope to the body of blocks preceded with the given prefix.
	#
	# @param prefixRe  Regular expression that specifies the prefix. It has to match all characters before `{`.
	# @param scopes    If present, the search is performed in the given *<scope>* collection, where *<scope>* 
    #                  is a tuple `(begin, end)` or `(begin, end, tag)`, `begin`, `end` are positions in the code 
	#                  and `tag` is anything.
	# @param tagFunc   Function that takes a @ref SourceMatch matching the prefix and a possibly tagged scope where 
	#                  the match occurred, and returns the tag for the new scope.
	# @param skipBlocks  If `True`, excludes blocks (any `{ ... }`) that start in the examined scopes from the search.
	# @return  `True` if the scopes were set, otherwise False.
	def tryScopeToBlockByPrefix(self, prefixRe, scopes=None, *, skipBlocks=True, tagFunc=(lambda _, __: None)):
		if scopes:
			oldScopes = self.__scopes
			self.setScopes(scopes)

		if skipBlocks:
			prefixPat = SourceFile.makeSkipBlocksPat(f"(?:{prefixRe}){{")
			find = self._findPatUnscoped_SkipBlocks
		else:
			prefixPat = regex.compile(f"(?:{prefixRe}){{")
			find = self._findPatUnscoped

		foundScopes = []

		pos = 0
		for scope in self.__scopes:
			(begin, end, _) = scope
			if begin is not None and pos < begin: 
				pos = begin
			while (end is None or pos < end) and (mres := find(prefixPat, pos, end)):
				pos = mres.end()
				blockEnd = self.__blockEnds[pos - 1]
				foundScopes.append((pos, blockEnd, tagFunc(sm.SourceRegexMatch(self, mres, copySource=False), scope)) )
				pos = blockEnd + 1

		if foundScopes:
			self.__scopes = foundScopes
			return True
		else:
			if scopes: self.__scopes = oldScopes
			return False


	## Returns the position for inserting a single line prefix in a block and the spacing that should be added around.
	#
	# @param begin  Valid position of a block beginning.
	# @param int    If `True`, the positions are internal.
	# @return       Triple `(hdspace, position, tlspace)`, where `position` is the position to insert and `hdspace`, 
	#               `tlspace` are spacing that should be added in front and behind to preserve the indentation.
	def blockSPrefixInsertPos(self, begin, *, int=False):
		if not int: begin = self.intPos(begin)
		assert begin in self.__blockEnds, "No block in the given position"
		blockEnd   = self.__blockEnds[begin]
		imres = self._matchPatUnscoped(_blockStartPat, begin + 1, blockEnd + 1)

		if imres.group("ins") is not None:
			pos = imres.start("ins")
			if not int: pos = self.orgPos(pos)

			if imres.group("del") == '}':
				return (imres.group("ind") + self.defaultIndent, pos, "\r\n")
			else:
				return (imres.group("ind"), pos, "\r\n")

		else:
			pos = imres.start("ins0")
			if not int: pos = self.orgPos(pos)

			if imres.group("del1") == '}':
				return ("", pos, imres.group("ind1"))
			elif (ind := imres.group("ind2")) is not None:
				return ("", pos, "\r\n" + ind)
			else:
				return ("", pos, " ")


	## Inserts a single line prefix in a block.
	#
	# The prefix should be not indented. The spacing and indentation is evaluated by SourceFile.blockSPrefixInsertPos. 
	def insertBlockSPrefix(self, prefix, begin, *, int=False):
		assert "\r\n" not in prefix, "Multiline prefix"
		if not int: begin = self.intPos(begin)
		(prefSpace, pos, sufSpace) = self.blockSPrefixInsertPos(begin, int=True)
		self.replaceMatch(sm.SourceRangeMatch(self, (pos, pos), int=True, copySource=False), 
					      prefSpace + prefix + sufSpace)


	def _blockExtension(self, ibegin, iend):
		if iend   is None: return len(self.__code)
		if ibegin is None: ibegin = 0
		iextpos = iend
		i = ibegin
		while i < iend:
			if self.__code[i] == '{':
				if range := self._getClipRange(i):
					i = range[1]
				else:
					blockEnd = self.__blockEnds[i]
					iextpos = max(iextpos, blockEnd)
					i = blockEnd
			else:
				i += 1
		return iextpos
	

	## Evaluates the position extending the given range to the longest block opened in it.
	def blockExtension(self, begin, end, *, int=False):
		if not int: 
			begin = self.intPos(begin)
			end   = self.intPos(end)
		iextpos = self._blockExtension(begin, end)
		return iextpos if int else self.orgPos(iextpos)
		
			
	def _recalcCode(self):
		self.__makeClipRangesAndLineEnds()
		self.__makeBlockEnds()


	def _lineJoinsBefore(self, pos):
		return bisect.bisect_right(self.__lineJoins, pos)


	def _lineJoinsOrgBefore(self, pos):
		return bisect.bisect_right(self.__lineJoinsOrg, pos)


	def __makeClipRangesAndLineEnds(self):
		self.__clipRanges = []
		self.__lineEnds = []

		pos = 0
		while (res := self.__nextClipAndLineEnds(pos)) and (clip := res[0]):
			pos = clip[1] + (2 if clip[2] == 'C' else 1)
			self.__clipRanges.append(clip)
			self.__lineEnds.extend(res[1])
		self.__lineEnds.extend(res[1])


	def __makeBlockEnds(self):
		self.__blockEnds = {}
		pos = 0
		begins = []
		while mres := self._findPatUnscoped(SourceFile.__blockEdgePat, pos):
			match mres.group():
				case '{': 
					begins.append(mres.start())
				case '}': 
					assert begins, f"{self.__filepath}:{self.orgPos(pos)}: }} has no match."
					self.__blockEnds[begins.pop()] = mres.start()
			pos = mres.end()

		assert begins == [], f"{self.__filepath}:{self.orgPos(begins[-1])}: {{ has no match."

	# __makeBlockEnds constants:
	__blockEdgePat = regex.compile(r"[\{}]")


	def __joinLines(self):
		self.__lineJoins = []
		self.__lineJoinsOrg = []
		def onMatch(m):
			self.__lineJoins.append(m.start() - 3*len(self.__lineJoins))
			self.__lineJoinsOrg.append(m.start())
			return ""
		self.__code = regex.sub(r"\\\r\n", onMatch, self.__code)


	def __recalc_lineJoinsOrg(self):
		newLineJoinsOrg = []
		shift = 0
		for pos in self.__lineJoins:
			newLineJoinsOrg.append(pos + shift)
			shift += 3
		self.__lineJoinsOrg = newLineJoinsOrg


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

		self.__lineJoins = list(reversed(newLineJoins))
		self.__recalc_lineJoinsOrg()


	def __nextClipAndLineEnds(self, start):
		lineEnds = []
		while (mres := _clipBeginPat.search(self.__code, start)) and mres.group() == "\r\n":
			lineEnds.append(mres.end())
			start = mres.end()

		if mres:
			match mres.group():
				case "'": 
					return ((mres.start() + 1, _endCharPat.search(self.__code, mres.end()).start(), 'h'), lineEnds)
				case '"':
					return ((mres.start() + 1, _endStrPat.search(self.__code, mres.end()).start(), 's'), lineEnds)
				case '//':
					mres2 = _endComment1Pat.search(self.__code, mres.end())
					return ((mres.end(), mres2.start(), 'c'), lineEnds + [mres2.end()])
				case '/*':
					start = mres.end()
					while (mres2 := _endCommentNOrNlPat.search(self.__code, start)) and \
							mres2.group() == "\r\n":
						lineEnds.append(mres2.end())
						start = mres2.end()
					return ((mres.end(), mres2.start(), 'C'), lineEnds)
				case _: # pragma: no cover
					assert False, mres

		return (None, lineEnds)