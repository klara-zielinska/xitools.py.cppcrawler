from . import sourcefile as sf
from . import sourcematch as sm
from . import sourcescopedict as ssd
import bisect
import regex
import os


## Dictionary class that stores @ref SourceMatch for further processing.
#  @anchor SourceMatchDict
#
# It inherits from `dict` where keys are @ref SourceFile and values are lists of either @ref SourceMatch or pairs 
# `(`@ref SourceMatch `, tag)` -- `tag` may be anything. The lists are ordered as inserted.
#
# A user is obligated to maintain the order in value lists if he manipulates them directly. For safe insertion see
# SourceMatchDict.insert.
class SourceMatchDict(dict):

    ## Contains information about missed searches in the form of a dictionary from @ref SourceFile to either pairs 
    # `(None, tag)` or `None` values -- depending on the tagging. Each item corresponds to one miss. This approach is 
    # chosen to allow processing uniformly with other items in the main dictionary (one can use the same
    # function to iterate over them). 
    missing = None


    ##
    # @param other   Dictionary to be copied. May be SourceMatchDict or other dictionary with the same structure. 
    #                In the latter case the it cannot contain key `None`.
    # @param tagged  Determines if matches should contain tags. If `None`, it is determined upon `other`.
    # @param sourceDir  The source directory -- used to determine relative paths.
    def __init__(self, other={}, *, tagged=None, sourceDir=None):
        super(SourceMatchDict, self).__init__()

        if isinstance(other, SourceMatchDict):
            assert tagged is None and not sourceDir
            self.__tagged    = other.__tagged
            self.__sourceDir = other.__sourceDir
            self.missing     = {}
            for src, matches in other.items():
                self[src] = matches.copy()
            for src, matches in other.missing.items():
                self.missing[src] = matches.copy()

        else:
            if not other:
                assert tagged is not None
            else:
                taggedChk = SourceMatchDict.isDictTagged(other)
                if tagged is None: tagged = taggedChk
                else:              assert tagged == taggedChk

            self.__tagged    = tagged
            self.__sourceDir = sourceDir
            self.missing     = {}
            for src, matches in other.items():
                assert isinstance(src, sf.SourceFile), "Illformed"
                assert isinstance(matches, list) and all(
                    SourceMatchDict.__istmatch(self.__tagged, m) for m in matches), "Illformed"
                self[src] = matches = matches.copy()
                matches.sort()
                

    def __istmatch(tagged, obj):
        if tagged:
            return type(obj) == tuple and len(obj) == 2 and isinstance(obj[0], sm.SourceMatch)
        else:
            return isinstance(obj, sm.SourceMatch)


    ## Produces a SourceMatchDict containing all matches form both dictionaries.
    def __add__(self, other):
        assert isinstance(other, SourceMatchDict) and self.__tagged == other.__tagged
        res = SourceMatchDict(self)
        for src in other:
            for match in other[src]:
                res.insert(src, match)
        return res


    ## Checks if the dictionary is tagged.
    def isTagged(self):
        return self.__tagged


    ## The source directory -- used to determine relative paths.
    def sourceDir(self):
        return self.__sourceDir


    ## Returns the key @ref SourceFile with the given file path.
    #
    # If the file path is relative and the source directory is set, the path is relative to this directory. Otherwise
    # relative paths are evaluated from the current directory.
    def getSource(self, filepath):
        if os.path.isabs(filepath):
            pass
        elif self.__sourceDir:
            filepath = os.path.abspath(self.__sourceDir + "/" + filepath)
        else:
            filepath = os.path.abspath(filepath)

        found = None
        for src in self:
            if src.filepath() == filepath:
                if found: raise EnvironmentError("Multiple sources")
                else:     found = src
        return found


    ## Inserts a match (preserves the matches order).
    #
    # @param src     The @ref SourceFile.
    # @param tmatch  @ref SourceMatch or pair `(`@ref SourceMatch `, tag)`. If the match is `None`, `tmatch` is
    #                appended in the `None` key in the `src` subkey.
    def insert(self, src, tmatch):
        assert not self.__tagged or type(tmatch) is tuple and len(tmatch) == 2
        if self.__tagged and not tmatch[0] or not tmatch:
            self.missing.setdefault(src, []).append(tmatch)
        else:
            bisect.insort(super().setdefault(src, []), tmatch)


    ## Filters matches of the dictionary.
    #
    # @param predicate  Function that if given @ref SourceFile and a possibly tagged @ref SourceMatch, determines
    #                   whether the match should be included.
    # @param new        If `True`, then instead modifying `self` a new dictionary is returned.
    # @return           The modified dictionary.
    def filter(self, predicate, *, new=False):
        if new:
            res = SourceMatchDict(tagged=self.__tagged)
            for src in self:
                if matches := [tm for tm in self[src] if predicate(src, tm)]:
                    res[src] = matches
            return res

        else:       
            toDel = []
            for src in self:
                if matches := [tm for tm in self[src] if predicate(src, tm)]:
                    self[src] = matches
                else:
                    toDel.append(src)
            for src in toDel:
                del self[src]
            return self

        
    ## Filters out matches that are not preceded with the given regular expression. See SourceMatchDict.filter.
    def filterPrecededWith(self, re, *, new=False):
        pat = regex.compile(f"(?<={re})")
        if self.isTagged():
            pred = lambda src, tm: pat.match(tm[0]._intCode(), tm[0].intStart())
        else:
            pred = lambda src, tm: pat.match(tm._intCode(), tm.intStart())

        return self.filter(pred, new=new)

    
    ## Filters out matches that are precoded with the given regular expression. See SourceMatchDict.filter.
    def filterNotPrecededWith(self, re, *, new=False):
        pat = regex.compile(f"(?<!{re})")
        if self.isTagged():
            pred = lambda src, tm: pat.match(tm[0]._intCode(), tm[0].intStart())
        else:
            pred = lambda src, tm: pat.match(tm._intCode(), tm.intStart())

        return self.filter(pred, new=new)


    ## Returns @ref SourceScopeDict with the scopes placed behind matches in `self`.
    #
    # If `self` if tagged, the tags are copied.
    def scopesBehind(self):
        scopes = ssd.SourceScopeDict(tagged=self.__tagged)
        if self.__tagged:
            for src in self:
                scopes[src] = list(map(lambda mt: (mt[0].end(), None, mt[1]), self[src]))
        else:
            for src in self:
                scopes[src] = list(map(lambda m: (m.end(), None), self[src]))
        return scopes
    

    ## Determines if a dictionary is tagged.
    #
    # @param d  SourceMatchDict or a non-empty `{`@ref SourceFile `: <tmatch> list }` where `<tmatch>` is a possibly 
    #           tagged @ref SourceMatch.
    def isDictTagged(d):
        if type(d) is SourceMatchDict:
            return d.isTagged()
        
        assert d, "Empty dictionary"

        tagged = None
        for src, matches in d.items():
            if not src: continue
            for m in matches:
                tagged = type(matches[0]) is tuple
                break
        assert tagged is not None, "Empty dictionary"

        for matches in d.values():
            for m in matches:
                if tagged:
                    assert type(m) is tuple and len(m) == 2 and isinstance(m[0], sm.SourceMatch),"Illformed dictionary"
                else:
                    assert isinstance(m, sm.SourceMatch)

        return tagged