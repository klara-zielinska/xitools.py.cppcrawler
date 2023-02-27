from . import sourcefile as sf
from . import sourcematch as sm
from . import sourcematchdict as smd
import bisect


# the author prefers to have int as a keyword parameter in some methods that also need the int type
_intType = int


## Dictionary class that stores source file scopes.
#  @anchor SourceScopeDict
#
# It inherits from `dict` where keys are @ref SourceFile and values are lists of either pairs `(start, end)` or
# triples `(start, end, tag)` -- `start`, `end` are original source file positions (see @ref SourceFile) and `tag` may 
# be anything. The lists are positionally ordered.
#
# A user is obligated to maintain the order in value lists if he manipulates them directly. For safe insertion see
# SourceMatchDict.insert.
class SourceScopeDict(dict):

    ##
    # @param other   Dictionary to be copied.
    # @param tagged  Determines if scopes should contain tags. If `None`, it is determined upon `other`.
    # @param int     If `True`, positions in `other` are taken as internal (see @ref SourceFile).
    def __init__(self, other={}, *, tagged=None, int=False):
        super(SourceScopeDict, self).__init__()

        if isinstance(other, SourceScopeDict):
            assert tagged is None
            self.__tagged    = other.__tagged
            for src, scopes in other.items():
                self[src] = scopes.copy()

        else:
            if not other:
                assert tagged is not None
            else:
                taggedChk = SourceScopeDict.isDictTagged(other)
                if tagged is None: tagged = taggedChk
                else:              assert tagged == taggedChk
            self.__tagged = tagged
        
            if int:
                def orgPos(src, pos): 
                    assert pos is None or type(pos) is _intType, f"Illformed: {pos}"
                    return src.orgPos(pos)
            else:
                def orgPos(src, pos): 
                    assert pos is None or type(pos) is _intType, f"Illformed: {pos}"
                    return pos
            
            for src, scopes in other.items():
                assert isinstance(src, sf.SourceFile) and isinstance(scopes, list), f"Illformed: {scopes}"
                self[src] = newScopes = []
                for scope in scopes:
                    assert type(scope) is tuple and len(scope) in [2, 3], f"Illformed: {scope}"
                    newScopes.append((orgPos(src, scope[0]), orgPos(src, scope[1])) + scope[2:])

                
    ## Produces a SourceScopeDict containing all scopes form both dictionaries.
    def __add__(self, other):
        assert isinstance(other, SourceScopeDict) and self.__tagged == other.__tagged
        res = SourceScopeDict(self)
        for src, scopes in other.items():
            for scope in scopes:
                res.insert(src, scope)
        return res

    
    ## Checks if the dictionary is tagged.
    def isTagged(self):
        return self.__tagged

    
    ## Inserts a scope.
    #
    # @param src     The @ref SourceFile.
    # @param scope   Pair `(start, end)` or triple `(start, end, tag)`, where `start`, `end` are original source file 
    #                positions (see @ref SourceFile) and `tag` may be anything.
    # @param int     If `True`, positions in `scope` are taken as internal (see @ref SourceFile).
    def insert(self, src, scope, *, int=False):
        assert len(scope) == 3 if self.__tagged else len(scope) == 2
        assert scope[0] is None or type(scope[0]) is _intType
        assert scope[1] is None or type(scope[1]) is _intType
        if int: scope = (src.orgPos(scope[0]), src.orgPos(scope[1])) + scope[2:]
        self.setdefault(src, []).append(scope)
        

    ## Matches all scopes against the given pattern and returns a @ref SourceMatchDict.
    #
    # Tags in the result are copied form the matched scopes.
    def matchEach(self, pat):
        d = smd.SourceMatchDict(tagged=self.isTagged())
        for src, scopes in self.items():
            for scope in scopes:
                mres = src.matchUnscoped(pat, scope[0], scope[1])
                if d.isTagged():
                    d.insert(src, (mres, scope[2]))
                else:
                    d.insert(src, mres)

        return d

    
    ## Determines if a dictionary is tagged.
    #
    # @param d  SourceScopeDict or a non-empty `{`@ref SourceFile `: <scope> list }` where *<scope>* is a pair 
    #           `(start, end)` or a triple `(start, end, tag)`, `start`, `end` are original source file positions 
    #           (see @ref SourceFile) and `tag` may be anything.
    def isDictTagged(d):
        if isinstance(d, SourceScopeDict):
            return d.isTagged()
        
        assert d, "Empty dictionary"

        tagged = None
        for scopes in d.values():
            for scope in scopes:
                tagged = type(scope) is tuple and len(scope) == 3
                break
        assert tagged is not None, "Empty dictionary"

        for scopes in d.values():
            for scope in scopes:
                assert type(scope) is tuple, f"Illformed dictionary: {scope}"
                if tagged:
                    assert len(scope) == 3, f"Illformed dictionary: {scope}"
                else:
                    assert len(scope) == 2, f"Illformed dictionary: {scope}"
                assert scope[0] is None or type(scope[0]) is int, f"Illformed dictionary: {scope}"
                assert scope[1] is None or type(scope[1]) is int, f"Illformed dictionary: {scope}"

        return tagged
