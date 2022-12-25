from . import sourcematch as sm
from . import sourcescopedict as ssd
import bisect
import regex


class SourceMatchDict(dict):

    def __init__(self, *arg, **kw):
        tagged = kw.pop('tagged', False)
        super(SourceMatchDict, self).__init__(*arg, **kw)
        self.__tagged = tagged


    def __add__(self, other):
        assert self.__tagged == other.__tagged
        res = SourceMatchDict(tagged=self.__tagged)
        for src in self:
            for match in self[src]:
                res.insert(src, match)
        for src in other:
            for match in other[src]:
                res.insert(src, match)
        return res


    def insert(self, src, match):
        assert not self.__tagged or len(match) >= 2
        bisect.insort(self.setdefault(src, []), match)


    def filter(self, predicate):
        res = SourceMatchDict(tagged=self.__tagged)
        for src in self:
            if matches := [tm for tm in self[src] if predicate(tm)]:
                res[src] = matches
        return res


    def precededWith(self, re):
        pat = regex.compile(f"(?<={re})")
        if self.isTagged():
            pred = lambda tm: pat.match(tm[0]._code(), tm[0]._intStart())
        else:
            pred = lambda tm: pat.match(tm._code(), tm._intStart())

        return self.filter(pred)


    def notPrecededWith(self, re):
        pat = regex.compile(f"(?<!{re})")
        if self.isTagged():
            pred = lambda tm: pat.match(tm[0]._code(), tm[0]._intStart())
        else:
            pred = lambda tm: pat.match(tm._code(), tm._intStart())

        return self.filter(pred)


    def isTagged(self):
        return self.__tagged


    def scopesBehind(self):
        scopes = ssd.SourceScopeDict(tagged=self.__tagged)
        if self.__tagged:
            for src in self:
                scopes[src] = list(map(lambda mt: (mt[0].end(), None, mt[1]), self[src]))
        else:
            for src in self:
                scopes[src] = list(map(lambda m: (m.end(), None), self[src]))
        return scopes