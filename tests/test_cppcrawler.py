from xitools.cppcrawler import CppCrawler
from xitools.cppcrawler import SourceFile
from xitools.cppcrawler import flatten
from unittest import TestCase
from tstutils import *
import filecmp


class CppCrawlerTests(TestCase):

    testSuit = "CppCrawlerTests"


    def setUpClass():
        prepareTmpDir(CppCrawlerTests.testSuit)
        os.mkdir(tmpFilepath(CppCrawlerTests.testSuit, "test_replaceSourceMatches"))


    def test_listSourceFiles(self):
        
        crawler = CppCrawler(dataFilepath("civ", None))

        self.assertEqual(crawler.listSourceFiles("algorithm2.h"), ["algorithm2.h"])

        self.assertEqual(set(crawler.listSourceFiles("*.h")), 
                         set(["algorithm2.h", "CvUnitSort.h", "CvPathGenerator.h"]))


    def test_loadSourceFiles(self):
        
        crawler = CppCrawler(dataFilepath("civ", None))

        self.assertEqual(set(map(lambda src: os.path.normpath(SourceFile.filename(src)), 
                                 crawler.loadSourceFiles(["algorithm2.h", "CvUnitSort.h"]))), 
                         set(map(os.path.normpath, 
                                 [dataFilepath("civ", "algorithm2.h"), dataFilepath("civ", "CvUnitSort.h")])))


    def test_findMethDeclarations(self):
        
        crawler = CppCrawler(dataFilepath("civ"))

        prots = ["UnitSortMove::getUnitValue(const%CvPlayer*, const%CvCity*, UnitTypes) const"]
        res = { cname: (src.filename(), mres.start()) 
                for cname, [(_, (src, mres))] 
                in crawler.findMethDeclarations(prots, "*.h", returnType='c').items() }
        self.assertEqual(res, { "UnitSortMove": (dataFilepath("civ", "CvUnitSort.h"), 1594) })
        
        
        prots = ["UnitSortMove::getUnitValue(const%CvPlayer*, const%CvCity*, UnitTypes) const",
                 "UnitSortCollateral::getUnitValue(const%CvPlayer*, const%CvCity*, UnitTypes) const",
                 "CvPathGeneratorBase::getTerminalPlot() const",
                 "foo()"]
        results = crawler.findMethDeclarations(prots, "*.h", returnType='c')
        self.assertEqual(set([(res[0].filename(), res[1].start()) if res else prot 
                              for (prot, res) in flatten(results.values())]), 
                         set([(dataFilepath("civ", "CvUnitSort.h"), 1594), 
                              (dataFilepath("civ", "CvUnitSort.h"), 1820),
                              (dataFilepath("civ", "CvPathGenerator.h"), 360),
                              "foo()"]))
        

        prots = ["UnitSortMove::getUnitValue(const%CvPlayer*, const%CvCity*, UnitTypes) const",
                 "UnitSortCollateral::getUnitValue(const%CvPlayer*, const%CvCity*, UnitTypes) const",
                 "CvPathGeneratorBase::getTerminalPlot() const",
                 "foo()"]
        results = crawler.findMethDeclarations(prots, "*.h", returnType='s')
        self.assertEqual(results[None], [(None, "foo()")])
        self.assertEqual(set([(mres.filename(), mres.start()) if mres else prot 
                              for (mres, prot) in flatten(results.values())]), 
                         set([(dataFilepath("civ", "CvUnitSort.h"), 1594), 
                              (dataFilepath("civ", "CvUnitSort.h"), 1820),
                              (dataFilepath("civ", "CvPathGenerator.h"), 360),
                              "foo()"]))
        

        prots = ["Incorrect::isInverse() const",]
        results = crawler.findMethDeclarations(prots, "CvUnitSort.h", returnType='s')
        self.assertEqual(results.pop(None, []), [(None, "Incorrect::isInverse() const")])
        self.assertEqual([(mres.filename(), mres.start()) if mres else prot 
                              for (mres, prot) in flatten(results.values())], 
                         [])
        

    def test_findMethDefinitions(self):
        
        crawler = CppCrawler(dataFilepath("mash"))

        prots = ["UnitSortMove::getUnitValue(const%CvPlayer*, const%CvCity*, UnitTypes) const"]
        res = crawler.findMethDefinitions(prots, "civ/CvUnitSort.cpp")
        self.assertEqual(res.pop(None, []), [])
        self.assertEqual([ (src.filename(), mres.start()) for src, [(mres, _)] in res.items() ], 
                         [ (dataFilepath("mash", "civ/CvUnitSort.cpp"), 1326) ])
        

        prots = ["UnitSortMove::getUnitValue(const%CvPlayer*, const%CvCity*, UnitTypes) const",
                 "foo()",
                 "TrivialA::bar(char, int)"]
        res = crawler.findMethDefinitions(prots, "**/*.*")
        self.assertEqual(res.pop(None, []), [(None, "foo()")])
        self.assertEqual(set([ (src.filename(), mres.start()) for src, [(mres, _)] in res.items() ]), 
                         set([ (dataFilepath("mash", "civ/CvUnitSort.cpp"), 1326), 
                               (dataFilepath("mash", "trivial.cpp"), 140) ]))

        
    def test_find(self):
        
        crawler = CppCrawler(dataFilepath("civ"))
        

        res = crawler.find([ "algo_functor" ], "*.h")
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : [ mres.start() for mres in results ]
                for src, results in res.items() }
        self.assertEqual(res, { dataFilepath("civ", "algorithm2.h") : [1672] })
        

        res = crawler.find([ "algo_functor" ], "*.h", skipBlocks=True)
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : [ mres.start() for mres in results ]
                for src, results in res.items() }
        self.assertEqual(res, { dataFilepath("civ", "algorithm2.h") : [6225] })
        

        res = crawler.find([ r"CvCity\*", r"bst::" ], "*.h")
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : [ mres.start() for mres in results ]
                for src, results in res.items() }
        self.assertEqual(res, { dataFilepath("civ", "CvUnitSort.h") : [3819],
                                dataFilepath("civ", "algorithm2.h") : [723] })


        res = crawler.find([ (r"CvCity\*", "city"), ("bst::", "boost"), ("!@#&%^rws", "mash") ], "*.h")
        self.assertEqual(res.pop(None, []), [(None, "mash")])
        res = { src.filename() : [ (mres.start(), tag) for (mres, tag) in results ]
                for src, results in res.items() }
        self.assertEqual(res, { dataFilepath("civ", "CvUnitSort.h") : [(3819, "city")],
                                dataFilepath("civ", "algorithm2.h") : [(723, "boost")] })
        
        
        res = crawler.find([ "struct", "CvCity" ], 
                           { "algorithm2.h" : [(1777, None)], 
                             "CvUnitSort.h" : [(None, 100), (3500, 3700)] })
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : [ mres.start() for mres in results ]
                for src, results in res.items() }
        self.assertEqual(res, { dataFilepath("civ", "CvUnitSort.h") : [3625],
                                dataFilepath("civ", "algorithm2.h") : [1793] })
        
        
        res = crawler.find([ ("struct|class", "cs"), ("template", "tm") ], 
                           { "algorithm2.h" : [(1598, None), (5581, None)], 
                             "CvUnitSort.h" : [(None, None)] },
                           perScope=True)
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ (mres and mres.start(), tag) for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set([(361, "cs"), (None, "tm")]),
              dataFilepath("civ", "algorithm2.h") : set([(1600, "tm"), (1611, "cs"), (5584, "tm"), (5595, "cs")]) })
        
        
        res = crawler.find([ "struct|class" ], 
                           { "algorithm2.h" : [(1598, None, "a1"), (5581, None, "a2")], 
                             "CvUnitSort.h" : [(None, None, "cus")] },
                           perScope=True)
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ (mres and mres.start(), tag) for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set([(361, "cus")]),
              dataFilepath("civ", "algorithm2.h") : set([(1611, "a1"), (5595, "a2")]) })
        
        
        res = crawler.find([ ("struct|class", "cs"), ("template", "tm") ], 
                           { "algorithm2.h" : [(1598, None, "a1"), (5581, None, "a2")], 
                             "CvUnitSort.h" : [(None, None, "cus")] },
                           perScope=True)
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ (mres and mres.start(), tag) for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set([(361, ("cs", "cus")), (None, ("tm", "cus"))]),
              dataFilepath("civ", "algorithm2.h") : set([(1600, ("tm", "a1")), (1611, ("cs", "a1")), 
                                                         (5584, ("tm", "a2")), (5595, ("cs", "a2"))]) })
        
        
        res = crawler.find([ ("struct|class", "cs"), ("template", "tm") ], 
                           { "algorithm2.h" : [(1598, None, "a1"), (5581, None, "a2")], 
                             "CvUnitSort.h" : [(None, None, "cus")] },
                           perScope=True, 
                           tagFunc = lambda mres, tpat, scope: tpat[1] + scope[2] + "_" + str(mres and mres.start()))
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ tag for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set(["cscus_361", "tmcus_None"]),
              dataFilepath("civ", "algorithm2.h") : set(["tma1_1600", "csa1_1611", 
                                                         "tma2_5584", "csa2_5595"]) })
        
        
        res = crawler.find([ "struct|class", "template" ], 
                           { "algorithm2.h" : [(1598, None), (5581, None)], 
                             "CvUnitSort.h" : [(None, None)] },
                           perScope=True, 
                           tagResult=True)
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ (mres and mres.start(), tag) for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set([(361, None), (None, None)]),
              dataFilepath("civ", "algorithm2.h") : set([(1600, None), (1611, None), 
                                                         (5584, None), (5595, None)]) })
        
        
        res = crawler.find([ "struct|class", "template" ], 
                           { "algorithm2.h" : [(1598, None), (5581, None)], 
                             "CvUnitSort.h" : [(None, None)] },
                           perScope=True, 
                           tagResult=True,
                           tagFunc = lambda mres, tpat, scope: 
                                         tpat.pattern + str(scope) + "_" + str(mres and mres.start()))
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ tag for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set(["struct|class(None, None)_361", "template(None, None)_None"]),
              dataFilepath("civ", "algorithm2.h") : set(["template(1598, None)_1600", "struct|class(1598, None)_1611", 
                                                         "template(5581, None)_5584", "struct|class(5581, None)_5595"])
              })
        
        
        res = crawler.find([ ("getUnitValue", "g") ], 
                           { "CvUnitSort.h" : [(None, None)], "CvUnitSort2.hpp" : [(None, None)] })
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ (mres and mres.start(), tag) for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set([(856, "g")]) })

        
    def test_findAll(self):
        
        crawler = CppCrawler(dataFilepath("civ"))
        

        res = crawler.findAll([ r"default_value(?=[\w<>:]*,)" ], "*.h")
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ mres.start() for mres in results ])
                for src, results in res.items() }
        self.assertEqual(res, { dataFilepath("civ", "algorithm2.h") : 
                                set([5732, 5887, 6036, 7055, 7640, 7708, 9014, 9623, 9691]) })
        

        res = crawler.findAll([ r"template<" ], "*.h", skipBlocks=True)
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ mres.start() for mres in results ])
                for src, results in res.items() }
        self.assertEqual(res, { dataFilepath("civ", "algorithm2.h") : 
                                set([694, 1212]) })
        
        
        res = crawler.findAll([ r"explicit", r"namespace" ], ["CvUnitSort.h", "algorithm2.h"])
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ mres.start() for mres in results ])
                for src, results in res.items() }
        self.assertEqual(res, { dataFilepath("civ", "CvUnitSort.h") : set([4087]),
                                dataFilepath("civ", "algorithm2.h") : set([1577, 5552, 10016]) })

        
        res = crawler.findAll([ (r"UnitSortList\* m_pList", "city"), ("bst::copy_backward", "boost"), 
                                ("!@#&%^rws", "mash") ], "*.h")
        self.assertEqual(res.pop(None, []), [(None, "mash")])
        res = { src.filename() : [ (mres.start(), tag) for (mres, tag) in results ]
                for src, results in res.items() }
        self.assertEqual(res, { dataFilepath("civ", "CvUnitSort.h") : [(4291, "city")],
                                dataFilepath("civ", "algorithm2.h") : [(10123, "boost")] })
        
        
        res = crawler.findAll([ "struct", "CvCity" ], 
                              { "algorithm2.h" : [(1777, 1800)], 
                                "CvUnitSort.h" : [(None, 400), (3500, 3700)] })
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ mres.start() for mres in results ])
                for src, results in res.items() }
        self.assertEqual(res, { dataFilepath("civ", "CvUnitSort.h") : set([367, 3625]),
                                dataFilepath("civ", "algorithm2.h") : set([1793]) })
        
        
        res = crawler.findAll([ ("(?:class|struct)(?![^<]*>)", "cs"), ("template", "tm") ], 
                              { "algorithm2.h" : [(5700, 6366)], 
                                "CvUnitSort.h" : [(None, 400)] })
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ (mres and mres.start(), tag) for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set([(361, "cs"), (376, "cs")]),
              dataFilepath("civ", "algorithm2.h") : set([(5700, "tm"), (5725, "cs"), (5855, "tm"), (5880, "cs"), 
                                                         (6001, "tm"), (6200, "cs"), ]) })
        
        
        res = crawler.findAll([ "struct|class" ], 
                              { "algorithm2.h" : [(1598, 1640, "a1"), (5581, 5610, "a2")], 
                                "CvUnitSort.h" : [(None, 400, "cus")] })
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ (mres and mres.start(), tag) for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set([(361, "cus"), (376, "cus")]),
              dataFilepath("civ", "algorithm2.h") : set([(1611, "a1"), (1627, "a1"), (5595, "a2")]) })
        
        
        res = crawler.findAll([ ("struct|class", "cs"), ("template", "tm") ], 
                              { "algorithm2.h" : [(1598, 1640, "a1"), (5581, 5610, "a2")], 
                                "CvUnitSort.h" : [(None, 400, "cus")] })
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ (mres and mres.start(), tag) for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set([(361, ("cs", "cus")), (376, ("cs", "cus"))]),
              dataFilepath("civ", "algorithm2.h") : set([(1600, ("tm", "a1")), (1611, ("cs", "a1")), 
                                                         (1627, ("cs", "a1")), (5584, ("tm", "a2")), 
                                                         (5595, ("cs", "a2"))]) })
        
        
        res = crawler.findAll([ ("struct|class", "cs"), ("template", "tm") ], 
                              { "algorithm2.h" : [(1598, 1640, "a1"), (5581, 5610, "a2")], 
                                "CvUnitSort.h" : [(None, 400, "cus")] },
                              tagFunc = lambda mres, tpat, scope: tpat[1] + scope[2] + "_" + str(mres and mres.start()))
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ tag for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set(["cscus_361", "cscus_376"]),
              dataFilepath("civ", "algorithm2.h") : set(["tma1_1600", "csa1_1611", 
                                                         "csa1_1627", "tma2_5584", 
                                                         "csa2_5595"]) })
        
        
        '''
        res = crawler.find([ "struct|class", "template" ], 
                           { "algorithm2.h" : [(1598, None), (5581, None)], 
                             "CvUnitSort.h" : [(None, None)] },
                           perScope=True, 
                           tagResult=True)
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ (mres and mres.start(), tag) for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set([(361, None), (None, None)]),
              dataFilepath("civ", "algorithm2.h") : set([(1600, None), (1611, None), 
                                                         (5584, None), (5595, None)]) })
        
        
        res = crawler.find([ "struct|class", "template" ], 
                           { "algorithm2.h" : [(1598, None), (5581, None)], 
                             "CvUnitSort.h" : [(None, None)] },
                           perScope=True, 
                           tagResult=True,
                           tagFunc = lambda mres, tpat, scope: 
                                         tpat.pattern + str(scope) + "_" + str(mres and mres.start()))
        self.assertEqual(res.pop(None, []), [])
        res = { src.filename() : set([ tag for (mres, tag) in results ])
                for src, results in res.items() }
        self.assertEqual(res, 
            { dataFilepath("civ", "CvUnitSort.h") : set(["struct|class(None, None)_361", "template(None, None)_None"]),
              dataFilepath("civ", "algorithm2.h") : set(["template(1598, None)_1600", "struct|class(1598, None)_1611", 
                                                         "template(5581, None)_5584", "struct|class(5581, None)_5595"])
              })
        '''


    def test_replaceSourceMatches(self):
        
        tmpdir = tmpFilepath(self.testSuit, "test_replaceSourceMatches")
        crawler = CppCrawler(dataFilepath("civ"))

        
        res = crawler.findAll( [ ("struct|class", "cs"), ("template", "tm") ], 
                               { "algorithm2.h" : [(1598, 1640, "a1"), (5581, 5610, "a2")], 
                                 "CvUnitSort.h" : [(None, 400, "cus")] })
        self.assertEqual(res.pop(None, []), [])
        crawler.replaceSourceMatches(res, lambda tm: tm[0].group(0) + f"/*{str(tm[1])}*/")

        for src in res:
            newfilename = os.path.join(tmpdir, os.path.basename(src.filename()))
            src.saveAs(newfilename, force=True)
            self.assertTrue(filecmp.cmp(src.filename(), newfilename))
