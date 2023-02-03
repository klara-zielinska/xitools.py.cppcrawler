from .sourcefile      import *
from .sourcematch     import *
from .sourcematchdict import *
from .sourcescopedict import *
from .utils           import *
from glob import glob
import os



## Class for processing C++ source files.
class CppCrawler:
    __sourceDir = None
    __backupDir = None


    ##
    # @param sourceDir  Root source directory.
    # @param encoding   Default encoding.
    # @param backupDir  Source backup directory.
    def __init__(self, sourceDir, encoding="utf-8-sig", *, backupDir=None):
        assert os.path.isdir(sourceDir)
        if backupDir:
            backupDir = os.path.abspath(backupDir)
            if os.path.exists(backupDir):
                assert os.path.isdir(backupDir)
            else:
                os.mkdir(backupDir)
        self.__sourceDir = sourceDir
        self.__backupDir = backupDir
        self.__encoding = encoding


    ## The source directory.
    def sourceDir(self):
        return self.__sourceDir


    ## The backup directory.
    def backupDir(self):
        self.__backupDir


    ## List of the paths to all backup bucket directories.
    #
    # The buckets are created in the backup directory whenever sources are saved through the crawler (see 
    # CppCrawler.saveSources). They are named with natural numbers: 0, 1, ... 
    def backupBucketDirs(self):
        buckets = []
        for dir in glob(os.path.join("*", ""), root_dir=self.__backupDir):
            dir = os.path.dirname(dir)
            if dir.isdigit() and (dir == "0" or not dir.startswith("0")):
                buckets.append(dir)
        buckets.sort(key=int)
        return [ os.path.join(self.__backupDir, dir) for dir in buckets ]


    ## Given a path or a SourceFile returns the path relative to the source directory.
    def sourceRelPath(self, file):
        if isinstance(file, SourceFile): file = file.filepath()
        return os.path.relpath(file, self.__sourceDir)

        
    ## Returns the list of files that match the path rooting from the source directory. Uses glob.
    def listSourceFiles(self, path):
        return glob(path, root_dir=self.__sourceDir, recursive=True)


    ## Loads and returns the source from the source directory as a SourceFile.
    #
    # If encoding=None, the crawler's is used.
    def loadSourceFile(self, filepath, encoding=None):
        if not encoding: encoding = self.__encoding
        return SourceFile(os.path.join(self.__sourceDir, filepath), encoding)


    ## Loads and returns sources from the source directory as a list of SourceFile-s.
    #
    # If encoding=None, the crawler's is used.
    def loadSourceFiles(self, paths, encodings=None):
        if type(paths) is str: paths = [paths]
        return [self.loadSourceFile(fname, encodings) for fname in flatten(map(self.listSourceFiles, paths))]
        

    ## Searches for method/function declarations.
    #
    # No namespace support.
    #
    # @param prots       Collection of method/function prototypes in the normal form (cf. Syntax module).
    # @param sources     Sources to search. A glob file path (e.g., "*.h"), a SourceFile, or a list of either.
    # @param returnType  Type of the returned value:
    #  's' - SourceMatchDict with prototypes being tags,
    #  'c' - dictionary { 'class name' : list[( 'prototype', (SourceFile, SourceMatch)|None )] }, 
    #  'l' - list[ ( 'prototype', (SourceFile, SourceMatch)|None ) ].
    # @return  Collection of matches. Matches align to found prototypes - e.g., fooBar( int i ).
    def findMethDeclarations(self, prots, sources, *, returnType='s'):
        protDict = CppCrawler.__makeMethProtsDict(prots)

        if isinstance(sources, SourceFile):
            sources = [sources]
        elif len(sources) > 0 and not isinstance(sources[0], SourceFile):
            sources = self.loadSourceFiles(sources)

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


    ## Searches for separated method/function definitions.
    #
    # No namespace support.
    #
    # @param sources  Sources to search. A glob file path (e.g., "*.h"), a SourceFile, or a list of either.
    # @return         SourceMatchDict with prototypes being tags, where matches align to found prototypes - e.g., 
    #                 fooBar( int i ).
    def findMethSepDefinitions(self, prots, sources):
        protReList = CppCrawler.__makeMethProtList(prots)
        
        if isinstance(sources, SourceFile):
            sources = [sources]
        elif len(sources) > 0 and not isinstance(sources[0], SourceFile):
            sources = self.loadSourceFiles(sources)
        
        return self.find(protReList, sources, skipBlocks=True)


    def __makeMethProtList(prots):
        protList = []
        for prot in prots:
            protPat = Syntax.makeMethProtRe(prot)
            protList.append((protPat, prot))
        return protList


    ## Finds one occurrence of each given pattern in sources.
    #
    # @param tpats    List of regex patterns or pairs (pattern, tag).
    # @param sources  Sources to be searched. A <source>, a collection of <source>, or a dict 
    #                 { <source> : <scope> collection }, where <source> is a path or a SourceFile, <scope> is a tuple
    #                 (begin, end) or (begin, end, tag), begin, end are positions in the file and tag is anything. The
    #                 dict can be a SourceScopeDict.
    # @param skipBlocks  If True, excludes blocks (any { ... }) that start in the examined scopes from the search.
    # @param perScope    If True, finds an occurence for each pattern in each given scope.
    # @param tagResult   Controls if the returned SourceMatchDict is tagged. Tags are evaluated by tagFunc.
    # @param tagFunc     Function that returns a tag for a result match. The first argument is a pattern that was 
    #                    matched or a pair (pattern, tag) - depending on the type of tpats. The second is a scope in 
    #                    which the match occurred - either (begin, end) or (begin, end, tag). If scopes were not given,
    #                    the default (None, None) is passed.
    # @return         A SourceMatchDict of results. Missing patterns are presented in 2 ways. If perScope=True, there 
    #                 is an entry for each missing pattern under the corresponding source key, otherwise the entry is
    #                 placed under the key None. If tagResult=True, the entries are pairs (None, tag), otherwise they 
    #                 are None-s. This approach is used to allow a uniform iteration over all elements in the dict.
    def find(self, tpats, sources, *, skipBlocks=False, perScope=False, tagResult=None, tagFunc=None):
        srcScopeDict = self.__find_makeSourceScopeDict(sources)
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
            find = (src._findPatUnscoped_SkipBlocks 
                    if skipBlocks else src._findPatUnscoped)
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
    

    def __defaultTagFuncTT(mres, tpat, scope):
        return (tpat[1], scope[2])


    def __defaultTagFuncTN(mres, tpat, scope):
        return tpat[1]


    def __defaultTagFuncNT(mres, tpat, scope):
        return scope[2]


    def __defaultTagFuncNN(mres, tpat, scope):
        return None


    def __find_makeSourceScopeDict(self, sources):
        if type(sources) is SourceScopeDict:
            srcScopeDict = sources
        elif type(sources) is dict:
            srcScopeDict = SourceScopeDict({ (s := src if type(src) is SourceFile else self.loadSourceFile(src)) : 
                             [ (s.intScope(scope), scope) for scope in scopes ]
                             for src, scopes in sources.items() })
        else:
            if type(sources) is str:
                sources = self.listSourceFiles(sources)
            srcScopeDict = SourceScopeDict({ (src if type(src) is SourceFile else self.loadSourceFile(src)) : 
                             [ ((None, None), (None, None)) ]
                             for src in sources })
        return srcScopeDict

    
    ## Finds all occurrences of the given patterns in sources.
    #
    # See the description of CppCrawler.find.
    def findAll(self, tpats, sources, *, tagResult=None, skipBlocks=False, tagFunc=None):
        srcScopeDict = self.__find_makeSourceScopeDict(sources)
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
            findAll = (src._findAllPat_Unscoped_SkipBlocks if skipBlocks 
                       else src._findAllPat_Unscoped)
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

    
    ## Replace all matches in a SourceMatchDict.
    # 
    # See SourceFile.replaceMatches.
    def replaceSourceMatches(self, mdict, repl):
        assert type(mdict) is SourceMatchDict
        for src in mdict:
            src.replaceMatches(mdict[src], repl, sorted=True)


    ## Saves a collection of SourceFile-s.
    #
    # Creates copies of the overwritten files a new bucket in the backup directory (see CppCrawler.backupBucketDirs). 
    def saveSources(self, sources, encoding=None):
        backupRoot = self._makeNextBackupBucket()
        for src in sources:
            backupDir = os.path.normpath(os.path.dirname(os.path.relpath(src.filepath(), self.__sourceDir)))
            assert not backupDir.startswith(".."), "Source files outside the source directory are unsupported"
            src.save(encoding, backupDir=os.path.join(backupRoot, backupDir), force=True)

    
    def _makeNextBackupBucket(self):
        buckets = []
        for dir in glob(os.path.join("*", ""), root_dir=self.__backupDir):
            dir = os.path.dirname(dir)
            if dir.isdigit() and (dir == "0" or not dir.startswith("0")):
                buckets.append(int(dir))
        nextBucketDir = os.path.join(self.__backupDir, str(max(buckets + [-1]) + 1))
        os.mkdir(nextBucketDir)
        return nextBucketDir
