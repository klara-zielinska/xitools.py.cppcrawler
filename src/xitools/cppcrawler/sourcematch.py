from . import sourcefile
from copy import copy


class SourceMatch:
    def __init__(self, sourcefile, mres):
        self.__sourcefile = copy(sourcefile)
        self.__mres = mres
        
    def filename(self):
        return self.__sourcefile.filename()

    def __getitem__(self, *groups):
        return self.__mres._Regex__getitem__(*groups)

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