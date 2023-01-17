from abc import ABC, abstractclassmethod


class SourceMatch(ABC):

    def __init__(self, sourcefile, copySource=True):
        self.__sourcefile = sourcefile.copy() if copySource else sourcefile

    def __getitem__(self, *groups):
        return self.group(*groups)

    def __lt__(self, other):
        if not self or not other: return False
        else:
            return (self._intStart(), self._intEnd()) < (other._intStart(), other._intEnd())

    def __eq__(self, other):
        if not self:    return self is other
        elif not other: return False
        else:
            return (self._intStart(), self._intEnd()) == (other._intStart(), other._intEnd())
        
    def __str__(self):
        return (f"<xitools.cppcrawler.sourcematch.SourceMatch object at {hex(id(self))}, "
                f"match='{self.group(0)}' start={self.startLoc()}, end={self.endLoc()}>")

    __repr__ = __str__

    def filename(self):
        return self.__sourcefile.filename()
    
    def group(self, *groups):
        if len(groups) == 1:
            return self._group1(groups[0])
        else:
            return tuple(self._group1(g) for g in groups)
    

    @abstractclassmethod
    def _group1(self, group):
        pass
    
    @abstractclassmethod
    def captures(self, group):
        pass
    
    @abstractclassmethod
    def start(self, group=0):
        pass
    
    @abstractclassmethod
    def end(self, group=0):
        pass
    
    @abstractclassmethod
    def startLoc(self, group=0):
        pass
    
    @abstractclassmethod
    def endLoc(self, group=0):
        pass

    def _code(self):
        return self.__sourcefile._code()
    
    @abstractclassmethod
    def _intStart(self, group=0):
        pass
    
    @abstractclassmethod
    def _intEnd(self, group=0):
        pass
    


class SourceRegexMatch(SourceMatch):

    def __init__(self, sourcefile, mres, *, copySource=True):
        assert mres
        SourceMatch.__init__(self, sourcefile, copySource)
        self.__mres = mres

    def _group1(self, group):
        return self.__mres.group(group)

    def group(self, *groups):
        return self.__mres.group(*groups)

    def captures(self, group):
        return self.__mres.captures(group)

    def start(self, group=0):
        return self._SourceMatch__sourcefile._orgPos(self.__mres.start(group))

    def end(self, group=0):
        return self._SourceMatch__sourcefile._orgPos(self.__mres.end(group))
    
    def startLoc(self, group=0):
        return self._SourceMatch__sourcefile._intOrgLocation(self.__mres.start(group))
    
    def endLoc(self, group=0):
        return self._SourceMatch__sourcefile._intOrgLocation(self.__mres.end(group))

    def _intStart(self, group=0):
        return self.__mres.start(group)

    def _intEnd(self, group=0):
        return self.__mres.end(group)
    


class SourceRangeMatch(SourceMatch):

    def __init__(self, src, ranges, *, intRanges=False, copySource=True):
        if isinstance(ranges, tuple):
            ranges = [ranges]
        if isinstance(ranges, list):
            self.__rangesDict = {}
            for i, (begin, end) in enumerate(ranges):
                assert 0 <= begin and begin <= end
                self.__rangesDict[i] =  (begin, end) if intRanges else (src._intPos(begin), src._intPos(end))
        elif isinstance(ranges, dict):
            assert 0 in ranges
            if intRanges:
                self.__rangesDict = ranges.copy()
            else:
                self.__rangesDict = {}
                for group, (begin, end) in ranges:
                    assert 0 <= begin and begin <= end
                    self.__rangesDict[group] = (src._intPos(begin), src._intPos(end))
        else:
            raise TypeError

        SourceMatch.__init__(self, src, copySource)


    def _group1(self, group):
        (begin, end) = self.__rangesDict[group]
        return self._SourceMatch__sourcefile._intCode()[begin:end]

    def captures(self, group):
        return [self._group1(group)]

    def start(self, group=0):
        return self._SourceMatch__sourcefile._orgPos(self.__rangesDict[group][0])

    def end(self, group=0):
        return self._SourceMatch__sourcefile._orgPos(self.__rangesDict[group][1])
    
    def startLoc(self, group=0):
        return self._SourceMatch__sourcefile._intOrgLocation(self.__rangesDict[group][0])
    
    def endLoc(self, group=0):
        return self._SourceMatch__sourcefile._intOrgLocation(self.__rangesDict[group][1])

    def _intStart(self, group=0):
        return self.__rangesDict[group][0]

    def _intEnd(self, group=0):
        return self.__rangesDict[group][1]
