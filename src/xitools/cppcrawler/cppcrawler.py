from .sourcefile      import *
from .sourcematch     import *
from .sourcematchdict import *
from .sourcescopedict import *
from .utils           import *
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
        return glob(filepath, root_dir=self.__sourceDir, recursive=True)


    def loadSourceFile(self, filename):
        return SourceFile(os.path.join(self.__sourceDir, filename))


    def loadSourceFiles(self, filenames):
        return list(map(self.loadSourceFile, flatten(map(self.listSourceFiles, filenames))))
        

    # sources - glob's file path pattern, e.g., "*.h" or a list of paths or a list SourceFile-s
    # returnType: 
    # 'c' - return dictionary { class_name : list[( prototype, (SourceFile, SourceMatch)|None )] }, 
    # 's' - SourceMatchDict with prototypes as tags,
    # 'l' - list[( prototype, (SourceFile, SourceMatch)|None )]
    def findMethDeclarations(self, prots, sources, *, returnType='s'):
        protDict = CppCrawler.__makeMethProtsDict(prots)

        if type(sources) is str:
            sources = self.listSourceFiles(sources)
        if len(sources) > 0 and type(sources[0]) is str:
            sources = [ SourceFile(os.path.join(self.__sourceDir, filename))
                        for filename in sources ]

        for src in sources:
            for cname in protDict:
                if not cname: 
                    src.resetScopes()
                elif not src.tryScopeToClassBody(cname, (None, None)):
                    continue

                for protRec in protDict[cname]:
                    [_, protPat, _] = protRec
                    if res := src.find(protPat):
                        assert not protRec[2], str(protRec)
                        protRec[2] = (src, res)
                     
        match returnType:
            case 's':
                d = SourceMatchDict(tagged=True)
                for recs in protDict.values():
                    for (prot, _, res) in recs:
                        if res:
                            d.setdefault(res[0], []).append((res[1], prot))
                        else:
                            d.setdefault(None, []).append((None, prot))
                return d

            case 'c':
                for cname in protDict:
                    protDict[cname] = [ (rec[0], rec[2]) for rec in protDict[cname] ]
                return protDict

            case 'l':
                return list(map(lambda rec: (rec[0], rec[2]), flatten(protDict.values())))

            case _:
                assert False, "Invalid returnType"

    
    # no namespaces support
    def __makeMethProtsDict(prots):
        protDict = {}
        for prot in prots:
            (cname, prot0) = Syntax.extractProtContainerName(prot)
            protPat = regex.compile(Syntax.makeMethProtRe(prot0))
            protDict.setdefault(cname, []).append([prot, protPat, None])
        return protDict


    def findMethDefinitions(self, prots, sources):
        protList = CppCrawler.__makeMethProtList(prots)

        if type(sources) is str:
            sources = self.listSourceFiles(sources)
        if len(sources) > 0 and type(sources[0]) is str:
            sources = [ SourceFile(os.path.join(self.__sourceDir, filename))
                        for filename in sources ]
        
        return self.find(protList, sources, skipBlocks=True)


    def __makeMethProtList(prots):
        protList = []
        for prot in prots:
            protPat = Syntax.makeMethProtRe(prot)
            protList.append((protPat, prot))
        return protList
        

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


    #def searchScopes(self, pat, srcScopeDict):
    #    d = SourceMatchDict(tagged=SourceScopeDict.isDictTagged(srcScopeDict))
    #    for src in srcScopeDict:
    #        d[src] = srcResults = []
    #        for scope in srcScopeDict[src]:
    #            mres = src.findUnscoped(pat, scope[0], scope[1])
    #            if mres:
    #                if d.isTagged():
    #                    srcResults.append((mres, scope[2]))
    #                else:
    #                    srcResults.append(mres)
    #    return d


    #def searchScopes_SkipBlocks(self, pat, srcScopeDict):
    #    d = SourceMatchDict(tagged=SourceScopeDict.isDictTagged(srcScopeDict))
    #    for src in srcScopeDict:
    #        d[src] = srcResults = []
    #        for scope in srcScopeDict[src]:
    #            mres = src.findUnscoped_SkipBlocks(pat, scope[0], scope[1])
    #            if mres:
    #                if d.isTagged():
    #                    srcResults.append((mres, scope[2]))
    #                else:
    #                    srcResults.append(mres)
    #    return d


    #def findAll(self, pat, sources):
    #    return self.findAllInScopes(pat, { src: [(None, None)] for src in sources })
    

    #def findAllInScopes(self, pat, srcScopeDict):
    #    d = SourceMatchDict(tagged=SourceScopeDict.isDictTagged(srcScopeDict))
    #    for src in srcScopeDict:
    #        d[src] = srcResults = []
    #        for scope in srcScopeDict[src]:
    #            results = src.findAllGenUnscoped(pat, scope[0], scope[1])
    #            if d.isTagged():
    #                srcResults += list(map(lambda mres: (mres, scope[2]), results))
    #            else:
    #                srcResults += results
    #    return d
    

    def __defaultTagFuncTT(mres, tpat, scope):
        return (tpat[1], scope[2])


    def __defaultTagFuncTN(mres, tpat, scope):
        return tpat[1]


    def __defaultTagFuncNT(mres, tpat, scope):
        return scope[2]


    def __defaultTagFuncNN(mres, tpat, scope):
        return None


    def _intScope(src, scope):
        return tuple([src._intPos(scope[0]), src._intPos(scope[1])] + ([scope[2]] if len(scope) >= 3 else []))
    

    def _orgScope(src, scope):
        return tuple([src._orgPos(scope[0]), src._orgPos(scope[1])] + ([scope[2]] if len(scope) >= 3 else []))


    def __makeSourceScopeDict(self, sources):
        if type(sources) is SourceScopeDict:
            srcScopeDict = sources
        elif type(sources) is dict:
            srcScopeDict = { (s := src if type(src) is SourceFile else self.loadSourceFile(src)) : 
                             [ (CppCrawler._intScope(s, scope), scope) for scope in scopes ]
                             for src, scopes in sources.items() }
        else:
            if type(sources) is str:
                sources = self.listSourceFiles(sources)
            srcScopeDict = { (src if type(src) is SourceFile else self.loadSourceFile(src)) : 
                             [ ((None, None), (None, None)) ]
                             for src in sources }
        return srcScopeDict


    def find(self, tpats, sources, *, tagResult=None, skipBlocks=False, perScope=False, tagFunc=None):
        srcScopeDict = self.__makeSourceScopeDict(sources)
        scopesTagged = srcScopeDict and len(next(iter(srcScopeDict.values()))[0][0]) == 3 # check len of first scope

        if not tpats:
            return SourceMatchDict(tagged=tagResult is None and scopesTagged or tagResult)
        elif type(tpats) is not list:
            tpats = [tpats]

        tpatsTagged = type(tpats[0]) is tuple
        if tagResult is None: tagResult = tpatsTagged or scopesTagged 

        if tpatsTagged:
            def tpatPat(tpat): return tpat[0]
            if not tagFunc:
                if scopesTagged: tagFunc = CppCrawler.__defaultTagFuncTT
                else:            tagFunc = CppCrawler.__defaultTagFuncTN
        else:
            def tpatPat(tpat): return tpat
            if not tagFunc:
                if scopesTagged: tagFunc = CppCrawler.__defaultTagFuncNT
                else:            tagFunc = CppCrawler.__defaultTagFuncNN
        if tagResult: 
            def tagMres(mres, tpat, scope): return (mres, tagFunc(mres, tpat, scope))
        else:
            def tagMres(mres, tpat, scope): return mres

        makePat = SourceFile.makeSkipBlocksPat if skipBlocks else regex.compile
        if tpatsTagged: 
            tpats = list(map(lambda tpat: (makePat(tpat[0]), tpat[1]), tpats))
        else:
            tpats = list(map(makePat, tpats))
            
        d = SourceMatchDict(tagged=tagResult)
        patsFound = [False] * len(tpats)

        for src in srcScopeDict:
            find = (src._SourceFile__findPatUnscoped_SkipBlocks 
                    if skipBlocks else src._SourceFile__findPatUnscoped)
            for (intScope, orgScope) in srcScopeDict[src]:
                for i, tpat in enumerate(tpats):
                    if not perScope and patsFound[i]: continue
                    if mres := find(tpatPat(tpat), intScope[0], intScope[1]):
                        d.insert(src, tagMres(SourceRegexMatch(src, mres), tpat, orgScope))
                        patsFound[i] = True
                    elif perScope:
                        d.insert(src, tagMres(None, tpat, orgScope))

        if not perScope:
            missings = []
            for i, tpat in enumerate(tpats):
                if not patsFound[i]: missings.append(tagMres(None, tpat, None))
            if missings: d[None] = missings

        return d


    def findAll(self, tpats, sources, *, tagResult=None, skipBlocks=False, tagFunc=None):
        srcScopeDict = self.__makeSourceScopeDict(sources)
        scopesTagged = srcScopeDict and len(next(iter(srcScopeDict.values()))[0][0]) == 3 # check len of first scope

        if not tpats:
            return SourceMatchDict(tagged=tagResult is None and scopesTagged or tagResult)
        elif type(tpats) is not list:
            tpats = [tpats]

        tpatsTagged = type(tpats[0]) is tuple
        if tagResult is None: tagResult = tpatsTagged or scopesTagged 

        if tpatsTagged:
            def tpatPat(tpat): return tpat[0]
            if not tagFunc:
                if scopesTagged: tagFunc = CppCrawler.__defaultTagFuncTT
                else:            tagFunc = CppCrawler.__defaultTagFuncTN
        else:
            def tpatPat(tpat): return tpat
            if not tagFunc:
                if scopesTagged: tagFunc = CppCrawler.__defaultTagFuncNT
                else:            tagFunc = CppCrawler.__defaultTagFuncNN
        if tagResult: 
            def tagMres(mres, tpat, scope): return (mres, tagFunc(mres, tpat, scope))
        else:
            def tagMres(mres, tpat, scope): return mres

        makePat = SourceFile.makeSkipBlocksPat if skipBlocks else regex.compile
        if tpatsTagged: 
            tpats = list(map(lambda tpat: (makePat(tpat[0]), tpat[1]), tpats))
        else:
            tpats = list(map(makePat, tpats))
            
        d = SourceMatchDict(tagged=tagResult)
        patsFound = [False] * len(tpats)

        for src in srcScopeDict:
            findAll = (src._SourceFile__findAllPatGen_Unscoped_SkipBlocks 
                       if skipBlocks else src._SourceFile__findAllPatGen_Unscoped)
            for (intScope, orgScope) in srcScopeDict[src]:
                for i, tpat in enumerate(tpats):
                    for mres in findAll(tpatPat(tpat), intScope[0], intScope[1]):
                        d.insert(src, tagMres(SourceRegexMatch(src, mres), tpat, orgScope))
                        patsFound[i] = True
            
        missings = []
        for i, tpat in enumerate(tpats):
            if not patsFound[i]: missings.append(tagMres(None, tpat, None))
        if missings: d[None] = missings

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
