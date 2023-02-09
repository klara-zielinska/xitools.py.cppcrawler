from xitools.cppcrawler import CppCrawler
from xitools.cppcrawler import SourceFile
from xitools.cppcrawler import flatten
from unittest import TestCase
from tstutils import *
import filecmp


class CppCrawlerTests(TestCase):
    
    maxDiff  = None
    testSuit = "CppCrawlerTests"


    def setUpClass():
        prepareTmpDir(CppCrawlerTests.testSuit)
        os.mkdir(tmpFilepath(CppCrawlerTests.testSuit, "test_replaceSourceMatches"))


    def test_sourceRelPath(self):

        crawler = CppCrawler(dataFilepath("mash", None))

        src = crawler.loadSourceFile("civ/CvUnitSort.h")

        self.assertEqual(crawler.sourceRelPath(src), os.path.normpath("civ/CvUnitSort.h"))


    def test_listSourceFiles(self):
        
        crawler = CppCrawler(dataFilepath("civ", None))

        self.assertEqual(crawler.listSourceFiles("algorithm2.h"), ["algorithm2.h"])

        self.assertEqual(set(crawler.listSourceFiles("*.h")), 
                         {"algorithm2.h", "CvUnitSort.h", "CvPathGenerator.h"})


    def test_loadSourceFiles(self):
        
        crawler = CppCrawler(dataFilepath("civ", None))

        self.assertEqual(set(map(lambda src: SourceFile.filepath(src), 
                                 crawler.loadSourceFiles(["algorithm2.h", "CvUnitSort.h"]))), 
                         { dataFilepath("civ", "algorithm2.h"), dataFilepath("civ", "CvUnitSort.h")})


    def test_findMethDeclarations(self):
        
        crawler = CppCrawler(dataFilepath("civ"))
        
        prots = ["UnitSortMove::getUnitValue(const`CvPlayer*, const`CvCity*, UnitTypes) const"]
        res = { cname: (src.filepath(), mres.start()) 
                for cname, [(_, (src, mres))] 
                in crawler.findMethDeclarations(prots, "*.h", returnType='c').items() }
        self.assertEqual(res, { "UnitSortMove": (dataFilepath("civ", "CvUnitSort.h"), 1594) })
        
        
        prots = ["UnitSortMove::getUnitValue(const`CvPlayer*, const`CvCity*, UnitTypes) const",
                 "UnitSortCollateral::getUnitValue(const`CvPlayer*, const`CvCity*, UnitTypes) const",
                 "CvPathGeneratorBase::getTerminalPlot() const",
                 "foo()"]
        results = crawler.findMethDeclarations(prots, "*.h", returnType='c')
        self.assertEqual([(res[0].filepath(), res[1].start()) if res else prot 
                              for (prot, res) in flatten(results.values())], 
                         [ (dataFilepath("civ", "CvUnitSort.h"), 1594), 
                           (dataFilepath("civ", "CvUnitSort.h"), 1820),
                           (dataFilepath("civ", "CvPathGenerator.h"), 360),
                           "foo()"])

        prots = ["UnitSortMove::getUnitValue(const`CvPlayer*, const`CvCity*, UnitTypes) const",
                 "UnitSortCollateral::getUnitValue(const`CvPlayer*, const`CvCity*, UnitTypes) const",
                 "CvPathGeneratorBase::getTerminalPlot() const",
                 "foo()"]
        results = crawler.findMethDeclarations(prots, "*.h", returnType='l')
        self.assertEqual([ (prot, (res and (res[0].filepath(), res[1].start())) ) for prot, res in results ], 
            [ ("UnitSortMove::getUnitValue(const`CvPlayer*, const`CvCity*, UnitTypes) const",
               (dataFilepath("civ", "CvUnitSort.h"), 1594)),
              ("UnitSortCollateral::getUnitValue(const`CvPlayer*, const`CvCity*, UnitTypes) const",
               (dataFilepath("civ", "CvUnitSort.h"), 1820)),
              ("CvPathGeneratorBase::getTerminalPlot() const",
               (dataFilepath("civ", "CvPathGenerator.h"), 360)),
              ("foo()", 
               None)])
        

        prots = ["UnitSortMove::getUnitValue(const`CvPlayer*, const`CvCity*, UnitTypes) const",
                 "UnitSortCollateral::getUnitValue(const`CvPlayer*, const`CvCity*, UnitTypes) const",
                 "CvPathGeneratorBase::getTerminalPlot() const",
                 "foo()"]
        results = crawler.findMethDeclarations(prots, "*.h", returnType='s')
        self.assertEqual(results.missing, { None : [(None, "foo()")] })
        self.assertEqual({ (mres.filepath(), mres.start()) if mres else prot 
                           for (mres, prot) in flatten(results.values()) }, 
                         { (dataFilepath("civ", "CvUnitSort.h"), 1594), 
                           (dataFilepath("civ", "CvUnitSort.h"), 1820),
                           (dataFilepath("civ", "CvPathGenerator.h"), 360) })
        

        prots = ["Incorrect::isInverse() const",]
        results = crawler.findMethDeclarations(prots, "CvUnitSort.h", returnType='s')
        self.assertEqual(results.missing, { None : [(None, "Incorrect::isInverse() const")] })
        self.assertEqual([(mres.filepath(), mres.start()) if mres else prot 
                              for (mres, prot) in flatten(results.values())], 
                         [])
        

    def test_findMethSepDefinitions(self):
        
        crawler = CppCrawler(dataFilepath("mash"))

        prots = ["UnitSortMove::getUnitValue(const`CvPlayer*, const`CvCity*, UnitTypes) const"]
        res = crawler.findMethSepDefinitions(prots, "civ/CvUnitSort.cpp")
        self.assertEqual(res.missing, {})
        self.assertEqual([ (src.filepath(), mres.start()) for src, [(mres, _)] in res.items() ], 
                         [ (dataFilepath("mash", "civ/CvUnitSort.cpp"), 1326) ])
        

        prots = ["UnitSortMove::getUnitValue(const`CvPlayer*, const`CvCity*, UnitTypes) const",
                 "foo()",
                 "TrivialA::bar(char, int)"]
        res = crawler.findMethSepDefinitions(prots, "**/*.*")
        self.assertEqual(res.missing, { None : [(None, "foo()")] })
        self.assertEqual(testMapSMD(lambda tmres: tmres[0].start(), res), 
                         { dataFilepath("mash", "civ/CvUnitSort.cpp") : [1326], 
                           dataFilepath("mash", "trivial.cpp") : [140] })
        
        
    def test_find(self):
        
        crawler = CppCrawler(dataFilepath("civ"))
        

        res = crawler.find([ "algo_functor" ], "*.h")
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda mres: mres.start(), res), 
                         { dataFilepath("civ", "algorithm2.h") : [1672] })
        

        res = crawler.find([ "algo_functor" ], "*.h", skipBlocks=True)
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda mres: mres.start(), res), 
                         { dataFilepath("civ", "algorithm2.h") : [6225] })
        

        res = crawler.find([ r"CvCity\*", r"bst::" ], "*.h")
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda mres: mres.start(), res), 
                         { dataFilepath("civ", "CvUnitSort.h") : [3819],
                           dataFilepath("civ", "algorithm2.h") : [723] })


        res = crawler.find([ (r"CvCity\*", "city"), ("bst::", "boost"), ("!@#&%^rws", "mash") ], "*.h")
        self.assertEqual(res.missing, { None : [(None, "mash")] })
        res = { src.filepath() : [ (mres.start(), tag) for (mres, tag) in results ]
                for src, results in res.items() }
        self.assertEqual(res, { dataFilepath("civ", "CvUnitSort.h") : [(3819, "city")],
                                dataFilepath("civ", "algorithm2.h") : [(723, "boost")] })
        
        
        res = crawler.find([ "struct", "CvCity" ], 
                           { "algorithm2.h" : [(1777, None)], 
                             "CvUnitSort.h" : [(None, 100), (3500, 3700)] })
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda mres: mres.start(), res), 
                         { dataFilepath("civ", "CvUnitSort.h") : [3625],
                           dataFilepath("civ", "algorithm2.h") : [1793] })
        
        
        res = crawler.find([ ("struct|class", "cs"), ("template", "tm") ], 
                           { "algorithm2.h" : [(1598, None), (5581, None)], 
                             "CvUnitSort.h" : [(None, None)] },
                           perScope=True)
        self.assertEqual(testMapSMD(lambda tmres: tmres[1], res.missing), 
                         { dataFilepath("civ", "CvUnitSort.h") : ["tm"] })
        self.assertEqual(testMapSMD(lambda tmres: (tmres[0].start(), tmres[1]), res), 
            { dataFilepath("civ", "CvUnitSort.h") : [(361, "cs")],
              dataFilepath("civ", "algorithm2.h") : [(1600, "tm"), (1611, "cs"), (5584, "tm"), (5595, "cs")] })
        
        
        res = crawler.find([ "struct|class" ], 
                           { "algorithm2.h" : [(1598, None, "a1"), (5581, None, "a2")], 
                             "CvUnitSort.h" : [(None, None, "cus")] },
                           perScope=True)
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda tmres: (tmres[0].start(), tmres[1]), res), 
            { dataFilepath("civ", "CvUnitSort.h") : [(361, "cus")],
              dataFilepath("civ", "algorithm2.h") : [(1611, "a1"), (5595, "a2")] })
        
        
        res = crawler.find([ ("struct|class", "cs"), ("template", "tm") ], 
                           { "algorithm2.h" : [(1598, None, "a1"), (5581, None, "a2")], 
                             "CvUnitSort.h" : [(None, None, "cus")] },
                           perScope=True)
        self.assertEqual(testMapSMD(lambda tmres: tmres[1], res.missing), 
                         { dataFilepath("civ", "CvUnitSort.h") : [ ("tm", "cus") ] })
        self.assertEqual(testMapSMD(lambda tmres: (tmres[0].start(), tmres[1]), res), 
            { dataFilepath("civ", "CvUnitSort.h") : [(361, ("cs", "cus"))],
              dataFilepath("civ", "algorithm2.h") : [(1600, ("tm", "a1")), (1611, ("cs", "a1")),
                                                     (5584, ("tm", "a2")), (5595, ("cs", "a2"))] })
        
        
        res = crawler.find([ ("struct|class", "cs"), ("template", "tm") ], 
                           { "algorithm2.h" : [(1598, None, "a1"), (5581, None, "a2")], 
                             "CvUnitSort.h" : [(None, None, "cus")] },
                           perScope=True, 
                           tagFunc = lambda mres, tpat, scope: tpat[1] + scope[2] + "_" + str(mres and mres.start()))
        self.assertEqual(testMapSMD(lambda tmres: tmres[1], res.missing),  
                         { dataFilepath("civ", "CvUnitSort.h") : ["tmcus_None"] })
        self.assertEqual(testMapSMD(lambda tmres: tmres[1], res), 
            { dataFilepath("civ", "CvUnitSort.h") : ["cscus_361"],
              dataFilepath("civ", "algorithm2.h") : ["tma1_1600", "csa1_1611", 
                                                     "tma2_5584", "csa2_5595"] })
        
        
        res = crawler.find([ "struct|class", "template" ], 
                           { "algorithm2.h" : [(1598, None), (5581, None)], 
                             "CvUnitSort.h" : [(None, None)] },
                           perScope=True, 
                           tagResult=True)
        self.assertEqual(testMapSMD(lambda tmres: tmres[1], res.missing),
                         { dataFilepath("civ", "CvUnitSort.h") : [None] })
        self.assertEqual(testMapSMD(lambda tmres: (tmres[0].start(), tmres[1]), res), 
            { dataFilepath("civ", "CvUnitSort.h") : [(361, None)],
              dataFilepath("civ", "algorithm2.h") : [(1600, None), (1611, None), 
                                                     (5584, None), (5595, None)] })
        
        
        res = crawler.find([ "struct|class", "template" ], 
                           { "algorithm2.h" : [(1598, None), (5581, None)], 
                             "CvUnitSort.h" : [(None, None)] },
                           perScope=True, 
                           tagResult=True,
                           tagFunc = lambda mres, tpat, scope: 
                                         tpat.pattern + str(scope) + "_" + str(mres and mres.start()))
        self.assertEqual(testMapSMD(lambda tmres: tmres[1], res.missing),
                         { dataFilepath("civ", "CvUnitSort.h") : ["template(None, None)_None"] })
        self.assertEqual(testMapSMD(lambda tmres: tmres[1], res), 
            { dataFilepath("civ", "CvUnitSort.h") : ["struct|class(None, None)_361"],
              dataFilepath("civ", "algorithm2.h") : ["template(1598, None)_1600", "struct|class(1598, None)_1611", 
                                                     "template(5581, None)_5584", "struct|class(5581, None)_5595"] })
        
        
        res = crawler.find([ ("getUnitValue", "g") ], 
                           { "CvUnitSort.h" : [(None, None)], "CvUnitSort2.hpp" : [(None, None)] })
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda tmres: (tmres[0].start(), tmres[1]), res), 
            { dataFilepath("civ", "CvUnitSort.h") : [(856, "g")] })

        
    def test_findAll(self):
        
        crawler = CppCrawler(dataFilepath("civ"))
        

        res = crawler.findAll([ r"default_value(?=[\w<>:]*,)" ], "*.h")
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda mres: mres.start(), res), 
                         { dataFilepath("civ", "algorithm2.h") : 
                           [5732, 5887, 6036, 7055, 7640, 7708, 9014, 9623, 9691] })
        

        res = crawler.findAll([ r"template<" ], "*.h", skipBlocks=True)
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda mres: mres.start(), res), 
                         { dataFilepath("civ", "algorithm2.h") : [694, 1212] })
        
        
        res = crawler.findAll([ r"explicit", r"namespace" ], ["CvUnitSort.h", "algorithm2.h"])
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda mres: mres.start(), res), 
                          { dataFilepath("civ", "CvUnitSort.h") : [4087],
                            dataFilepath("civ", "algorithm2.h") : [1577, 5552, 10016] })

        
        res = crawler.findAll([ (r"UnitSortList\* m_pList", "city"), ("bst::copy_backward", "boost"), 
                                ("!@#&%^rws", "mash") ], "*.h")
        self.assertEqual(res.pop(None, []), [(None, "mash")])
        
        self.assertEqual(testMapSMD(lambda tmres: (tmres[0].start(), tmres[1]), res), 
                         { dataFilepath("civ", "CvUnitSort.h") : [(4291, "city")],
                           dataFilepath("civ", "algorithm2.h") : [(10123, "boost")] })
        
        
        res = crawler.findAll([ "struct", "CvCity" ], 
                              { "algorithm2.h" : [(1777, 1800)], 
                                "CvUnitSort.h" : [(None, 400), (3500, 3700)] })
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda mres: mres.start(), res), 
                         { dataFilepath("civ", "CvUnitSort.h") : [367, 3625],
                           dataFilepath("civ", "algorithm2.h") : [1793] })
        
        
        res = crawler.findAll([ ("(?:class|struct)(?![^<]*>)", "cs"), ("template", "tm") ], 
                              { "algorithm2.h" : [(5700, 6366)], 
                                "CvUnitSort.h" : [(None, 400)] })
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda tmres: (tmres[0].start(), tmres[1]), res), 
            { dataFilepath("civ", "CvUnitSort.h") : [(361, "cs"), (376, "cs")],
              dataFilepath("civ", "algorithm2.h") : [(5700, "tm"), (5725, "cs"), (5855, "tm"), (5880, "cs"), 
                                                     (6001, "tm"), (6200, "cs"), ] })
        
        
        res = crawler.findAll([ "struct|class" ], 
                              { "algorithm2.h" : [(1598, 1640, "a1"), (5581, 5610, "a2")], 
                                "CvUnitSort.h" : [(None, 400, "cus")] })
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda tmres: (tmres[0].start(), tmres[1]), res), 
            { dataFilepath("civ", "CvUnitSort.h") : [(361, "cus"), (376, "cus")],
              dataFilepath("civ", "algorithm2.h") : [(1611, "a1"), (1627, "a1"), (5595, "a2")] })
        
        
        res = crawler.findAll([ ("struct|class", "cs"), ("template", "tm") ], 
                              { "algorithm2.h" : [(1598, 1640, "a1"), (5581, 5610, "a2")], 
                                "CvUnitSort.h" : [(None, 400, "cus")] })
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda tmres: (tmres[0].start(), tmres[1]), res), 
            { dataFilepath("civ", "CvUnitSort.h") : [(361, ("cs", "cus")), (376, ("cs", "cus"))],
              dataFilepath("civ", "algorithm2.h") : [(1600, ("tm", "a1")), (1611, ("cs", "a1")), 
                                                     (1627, ("cs", "a1")), (5584, ("tm", "a2")), 
                                                     (5595, ("cs", "a2"))] })
        
        
        res = crawler.findAll([ ("struct|class", "cs"), ("template", "tm") ], 
                              { "algorithm2.h" : [(1598, 1640, "a1"), (5581, 5610, "a2")], 
                                "CvUnitSort.h" : [(None, 400, "cus")] },
                              tagFunc = lambda mres, tpat, scope: tpat[1] + scope[2] + "_" + str(mres and mres.start()))
        self.assertEqual(res.missing, {})
        self.assertEqual(testMapSMD(lambda tmres: tmres[1], res), 
            { dataFilepath("civ", "CvUnitSort.h") : ["cscus_361", "cscus_376"],
              dataFilepath("civ", "algorithm2.h") : ["tma1_1600", "csa1_1611", 
                                                     "csa1_1627", "tma2_5584", 
                                                     "csa2_5595"] })
        

    def test_replaceSourceMatches(self):
        
        tmpdir = tmpFilepath(self.testSuit, "test_replaceSourceMatches")
        crawler = CppCrawler(dataFilepath("civ"))

        
        res = crawler.findAll( [ ("struct|class", "cs"), ("template", "tm") ], 
                               { "algorithm2.h" : [(1598, 1640, "a1"), (5581, 5610, "a2")], 
                                 "CvUnitSort.h" : [(None, 400, "cus")] })
        self.assertEqual(res.missing, {})
        crawler.replaceSourceMatches(res, lambda tm: tm[0].group(0) + f"/*{str(tm[1])}*/")

        for src in res:
            newfilepath = os.path.join(tmpdir, os.path.basename(src.filepath()))
            src.saveAs(newfilepath, force=True)
            self.assertTrue(filecmp.cmp(src.filepath(), newfilepath))


    def test_saveSources(self):
        
        srcdir = tmpFilepath(self.testSuit, "test_saveSources")
        backupdir = tmpFilepath(self.testSuit, "test_saveSources_backup")

        os.mkdir(srcdir)
        shutil.copy(dataFilepath("civ", "algorithm2.h"), srcdir)
        shutil.copy(dataFilepath("civ", "CvUnitSort.h"), srcdir)

        crawler = CppCrawler(srcdir, backupDir=backupdir)
        srcs = crawler.loadSourceFiles("*")
        for src in srcs:
            src.replace("^", "//test\r\n", 1)
        crawler._makeNextBackupBucket() # creating a dummy bucket for test coverage
        crawler.saveSources(srcs, encoding="utf-8")
        
        self.assertTrue(filecmp.cmp(tmpFilepath(self.testSuit, "test_saveSources/algorithm2.h"),
                                    dataFilepath("results", "algorithm2_saveSources.h")))
        self.assertTrue(filecmp.cmp(tmpFilepath(self.testSuit, "test_saveSources/CvUnitSort.h"),
                                    dataFilepath("results", "CvUnitSort_saveSources.h")))
        self.assertTrue(filecmp.cmp(os.path.join(crawler.backupBucketDirs()[1], "algorithm2.h"), 
                                    dataFilepath("civ", "algorithm2.h")))
        self.assertTrue(filecmp.cmp(os.path.join(crawler.backupBucketDirs()[1], "CvUnitSort.h"),
                                    dataFilepath("civ", "CvUnitSort.h")))
