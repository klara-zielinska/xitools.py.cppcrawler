from . import sourcematch as sm
from . import sourcescopedict as ssd
import bisect
import regex
import os


class SourceMatchDict(dict):

    class Iterator:
        def __init__(self, it):
            self.__it = it

        def __next__(self):
            return res if (res := next(self.__it)) else next(self.__it)


    def __init__(self, *arg, **kw):
        tagged = kw.pop('tagged', False)
        self.__sourceDir = kw.pop('sourceDir', None)
        super(SourceMatchDict, self).__init__(*arg, **kw)
        self.__tagged = tagged


    def __iter__(self):
        return SourceMatchDict.Iterator(iter(self.keys()))


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


    def sourceDir(self):
        return self.__sourceDir


    def insert(self, src, tmatch):
        assert not self.__tagged or len(tmatch) == 2
        if self.__tagged and not tmatch[0] or not tmatch:
            self.setdefault(src, []).insert(0, tmatch)
        else:
            bisect.insort(self.setdefault(src, []), tmatch)


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


    def getSource(self, filepath):
        if self.__sourceDir:
            filepath = os.path.abspath(self.__sourceDir + "/" + filepath)
        else:
            filepath = os.path.abspath(filepath)
        found = None
        for src in self:
            if src.filename() == filepath:
                if found: raise EnvironmentError("Multiple sources")
                else:     found = src
        return found
