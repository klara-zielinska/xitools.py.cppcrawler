from .sourcefile import *
from .utils import *
import glob
import os

class CppCrawler:
    __sourceDir = None


    def __init__(self, sourceDir):
        self.__sourceDir = sourceDir


    def sourceDir(self):
        return self.__sourceDir

        
    def listSourceFiles(self, filepath):
        return glob.glob(filepath, root_dir=self.__sourceDir)


    def loadSourceFile(self, filename):
        return SourceFile(os.path.join(self.__sourceDir, filename))
        

    # sourcePattern - glob file path, e.g., "*.h"
    def findMethDeclarations(self, prots, sourcePattern):
        protDict = CppCrawler.__makeMethProtsDict(prots)

        for filename in self.listSourceFiles(sourcePattern):
            src = SourceFile(os.path.join(self.__sourceDir, filename))
            selectedClass = None
            for cname, protRecs in protDict.items():

                if selectedClass != cname:
                    if not cname: 
                        src.resetScope()
                    elif src.tryScopeToClassBody(cname, (None, None)) < 0: # if class not found
                        continue
                    selectedClass = cname

                for protRec in protRecs:
                    [_, protPat, _] = protRec
                    if res := src.find(protPat):
                        protRec[2] = (filename, res)
                        
        return list(map(lambda rec: (rec[0], rec[2]), flatten(protDict.values())))

    
    def __makeMethProtsDict(prots):
        protDict = {}
        for p in prots:
            (cname, p0) = Syntax.extractMethProtClass(p)
            protPat = regex.compile(Syntax.makeMethProtRe(p0))
            protDict.setdefault(cname, []).append([p, protPat, None])
        return protDict
