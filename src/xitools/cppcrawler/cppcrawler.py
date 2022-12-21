from .sourcefile import *
from .sourcematchdict import *
from .sourcescopedict import *
from .utils import *
from glob import glob
import os

class CppCrawler:
    __sourceDir = None
    __backupDir = None


    def __init__(self, sourceDir, *, backupDir=None):
        assert os.path.isdir(sourceDir)
        if backupDir:
            if os.path.exists(backupDir):
                assert os.path.isdir(backupDir)
            else:
                os.mkdir(backupDir)
        self.__sourceDir = sourceDir
        self.__backupDir = backupDir


    def sourceDir(self):
        return self.__sourceDir

        
    def listSourceFiles(self, filepath):
        return glob(filepath, root_dir=self.__sourceDir)


    def loadSourceFile(self, filename):
        return SourceFile(os.path.join(self.__sourceDir, filename))


    def loadSourceFiles(self, filenames):
        return list(map(self.loadSourceFile, filenames))
        

    # sourcePattern - glob's file path, e.g., "*.h"
    # return: collection of pairs: prototype - match, the type depends on returnDict
    # returnDict: 'c' - dictionary per class name, 's' - dictionary per source file, False - list
    def findMethDeclarations(self, prots, sourcePattern, *, returnDict='c'):
        protDict = CppCrawler.__makeMethProtsDict(prots)

        for filename in self.listSourceFiles(sourcePattern):
            src = SourceFile(os.path.join(self.__sourceDir, filename))
            for cname in protDict:
                if not cname: 
                    src.resetScopes()
                elif src.tryScopeToClassBody(cname, (None, None)) < 0: # if class not found
                    continue

                for protRec in protDict[cname]:
                    [_, protPat, _] = protRec
                    if res := src.find(protPat):
                        protRec[2] = (src, res)
                     
        match returnDict:
            case 'c':
                for cname in protDict:
                    protDict[cname] = list(map(lambda rec: (rec[0], rec[2]), protDict[cname]))
                return protDict

            case 's':
                d = {}
                for recs in protDict.values():
                    for (prot, _, res) in recs:
                        if res:
                            d.setdefault(res[0], []).append((prot, res[1]))
                        else:
                            d.setdefault(None, []).append(prot)
                return d

            case False:
                return list(map(lambda rec: (rec[0], rec[2]), flatten(protDict.values())))

            case _:
                assert False, "Invalid returnDict"

    
    def __makeMethProtsDict(prots):
        protDict = {}
        for p in prots:
            (cname, p0) = Syntax.extractMethProtClass(p)
            protPat = regex.compile(Syntax.makeMethProtRe(p0))
            protDict.setdefault(cname, []).append([p, protPat, None])
        return protDict


    def matchScopes(self, pat, srcScopeDict):
        d = SourceMatchDict(tagged=SourceScopeDict.isDictTagged(srcScopeDict))
        for src in srcScopeDict:
            d[src] = srcResults = []
            for scope in srcScopeDict[src]:
                mres = src.matchUnscoped(pat, scope[0], scope[1])
                if mres:
                    if d.isTagged():
                        srcResults.append((mres, scope[2]))
                    else:
                        srcResults.append(mres)
        return d


    def searchScopes(self, pat, srcScopeDict):
        d = SourceMatchDict(tagged=SourceScopeDict.isDictTagged(srcScopeDict))
        for src in srcScopeDict:
            d[src] = srcResults = []
            for scope in srcScopeDict[src]:
                mres = src.findUnscoped(pat, scope[0], scope[1])
                if mres:
                    if d.isTagged():
                        srcResults.append((mres, scope[2]))
                    else:
                        srcResults.append(mres)
        return d


    def searchScopes_SkipBlocks(self, pat, srcScopeDict):
        d = SourceMatchDict(tagged=SourceScopeDict.isDictTagged(srcScopeDict))
        for src in srcScopeDict:
            d[src] = srcResults = []
            for scope in srcScopeDict[src]:
                mres = src.findUnscoped_SkipBlocks(pat, scope[0], scope[1])
                if mres:
                    if d.isTagged():
                        srcResults.append((mres, scope[2]))
                    else:
                        srcResults.append(mres)
        return d


    def findAll(self, pat, sources):
        return self.findAllInScopes(pat, { src: [(None, None)] for src in sources })
    

    def findAllInScopes(self, pat, srcScopeDict):
        d = SourceMatchDict(tagged=SourceScopeDict.isDictTagged(srcScopeDict))
        for src in srcScopeDict:
            d[src] = srcResults = []
            for scope in srcScopeDict[src]:
                results = src.findAllGenUnscoped(pat, scope[0], scope[1])
                if d.isTagged():
                    srcResults += list(map(lambda mres: (mres, scope[2]), results))
                else:
                    srcResults += results
        return d

    
    def replaceSourceMatches(self, ms, repl):
        assert type(ms) is SourceMatchDict
        for src in ms:
            src.replaceMatches(ms[src], repl, sorted=True)


    def saveSources(self, sources):
        backupRoot = self.__makeNextBackupBucket()
        for src in sources:
            backupDir = os.path.normpath(os.path.dirname(os.path.relpath(src.filename(), self.__sourceDir)))
            assert not backupDir.startswith(".."), "Source files outside the source directory are unsupported"
            src.save(backupDir=os.path.join(backupRoot, backupDir), force=True)

    
    def __makeNextBackupBucket(self):
        buckets = []
        for dir in glob(os.path.join("*", ""), root_dir=self.__backupDir):
            try:
                buckets.append(int(os.path.dirname(dir)))
            except ValueError:
                pass
        nextBucketDir = os.path.join(self.__backupDir, str(max(buckets + [-1]) + 1))
        os.mkdir(nextBucketDir)
        return nextBucketDir