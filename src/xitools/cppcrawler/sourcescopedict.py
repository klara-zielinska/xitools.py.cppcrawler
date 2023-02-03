from . import sourcefile as sf
from . import sourcematch as sm
from . import sourcematchdict as smd
import bisect


class SourceScopeDict(dict):

    def __init__(self, other={}, *, tagged=None):
        if type(other) is SourceScopeDict:
            assert tagged is None
            self.__tagged = other.__tagged
        else:
            if other:
                othTagged = SourceScopeDict.isDictTagged(other)
                assert tagged is None or othTagged == tagged
                self.__tagged = othTagged
            else:
                assert tagged is not None
                self.__tagged = tagged
        super(SourceScopeDict, self).__init__(other)


    def __add__(self, other):
        assert self.__tagged == other.__tagged
        res = SourceScopeDict(tagged=self.__tagged)
        for src in self:
            for scope in self[src]:
                res.insert(src, scope)
        for src in other:
            for scope in other[src]:
                res.insert(src, scope)
        return res


    def insert(self, src, scope):
        assert not self.__tagged or len(scope) >= 3
        bisect.insort(self.setdefault(src, []), scope)


    def isTagged(self):
        return self.__tagged


    def isDictTagged(d):
        if type(d) is SourceScopeDict:
            return d.isTagged()
        for src in d:
            for scope in d[src]:
                return len(scope) >= 3
        assert False, "Dictionary cannot be empty"
        

    def match(self, pat):
        d = sm.SourceMatchDict(tagged=self.isTagged())
        for src in self:
            d[src] = srcResults = []
            for scope in self[src]:
                mres = src.matchUnscoped(pat, scope[0], scope[1])
                if d.isTagged():
                    srcResults.append((mres, scope[2]))
                else:
                    srcResults.append(mres)
        return d
