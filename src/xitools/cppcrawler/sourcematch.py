from . import sourcefile as sf


class SourceMatch:
    def __init__(self, sourcefile, mres, *, copySource=True):
        assert mres
        self.__sourcefile = sourcefile._matchShellCopy() if copySource else sourcefile
        self.__mres = mres

    def __getitem__(self, *groups):
        return self.__mres.__getitem__(*groups)

    def __lt__(self, other):
        return (self.__mres.start(), self.__mres.end()) < (other.__mres.start(), other.__mres.end())

    def __eq__(self, other):
        return (self.__mres.start(), self.__mres.end()) == (other.__mres.start(), other.__mres.end())
        
    def __str__(self):
        return (f"<xitools.cppcrawler.sourcematch.SourceMatch object at {hex(id(self))}, "
                f"match='{self.group(0)}' start={self.startLoc()}, end={self.endLoc()}>")

    __repr__ = __str__

    def filename(self):
        return self.__sourcefile.filename()

    def group(self, *groups):
        return self.__mres.group(*groups)

    def captures(self, group):
        return self.__mres.captures(group)

    def start(self, group=0):
        return self.__sourcefile._orgPos(self.__mres.start(group))

    def end(self, group=0):
        return self.__sourcefile._orgPos(self.__mres.end(group))
    
    def startLoc(self, group=0):
        return self.__sourcefile._intOrgLocation(self.__mres.start(group))
    
    def endLoc(self, group=0):
        return self.__sourcefile._intOrgLocation(self.__mres.end(group))