from xitools.cppcrawler import SourceFile, SourceScopeDict
from unittest import TestCase
from tstutils import *


class SourceScopeDictTests(TestCase):
    
    maxDiff  = None
    testSuit = "SourceScopeDictTests"


    def setUpClass():
        prepareTmpDir(SourceScopeDictTests.testSuit)


    def test___init__(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceScopeDict(tagged=False), {})
        self.assertEqual(SourceScopeDict(tagged=True),  {})
        self.assertEqual(SourceScopeDict({ src : [(1, 2, "tag")] }, tagged=True),  { src : [(1, 2, "tag")] })
        self.assertEqual(SourceScopeDict({ src : [(1, 2)] },        tagged=False), { src : [(1, 2)] })
        self.assertEqual(SourceScopeDict({ src : [(691, 717)] },        int=True), { src : [(694, 723)] })
        self.assertEqual(SourceScopeDict({ src : [(691, 717, "tag")] }, int=True), { src : [(694, 723, "tag")] })

        self.assertRaises(AssertionError, SourceScopeDict, { src : [(1, 2)] },        tagged=True)
        self.assertRaises(AssertionError, SourceScopeDict, { src : [(1, 2, "tag")] }, tagged=False)
        self.assertRaises(AssertionError, SourceScopeDict, { src : [(1, 2), (1, 2, "tag")] }, tagged=False)
        self.assertRaises(AssertionError, SourceScopeDict, { src : [(1, 2), (1, 2, "tag")] }, tagged=True)
        self.assertRaises(AssertionError, SourceScopeDict, { src : [(1, 2), (1, 2, "tag")] })
        
        ssd = SourceScopeDict({ src : [(2, 4), (1, 2)] })
        self.assertEqual(ssd, { src : [(2, 4), (1, 2)] })
        self.assertEqual(ssd.isTagged(), False)

        ssd = SourceScopeDict({ src : [(2, 4, "a"), (1, 2, "b")] })
        self.assertEqual(ssd, { src : [(2, 4, "a"), (1, 2, "b")] })
        self.assertEqual(ssd.isTagged(), True)

        
    def test___add__(self):

        src1 = SourceFile(dataFilepath("civ", "algorithm2.h"))
        src2 = SourceFile(dataFilepath("civ", "CvUnitSort.h"))

        ssd1 = SourceScopeDict({ src1 : [(2, 4), (1, 2)] })
        ssd2 = SourceScopeDict({ src1 : [(691, 717)] }, int=True)
        ssd3 = SourceScopeDict({ src1 : [(1, 3 ,"tag1")] })
        ssd4 = SourceScopeDict({ src1 : [(2, 4, "tag2"), (1, 2, "tag3")] })
        ssd5 = SourceScopeDict({ src2 : [(None, 3, "tag4")] })
        
        self.assertEqual(ssd1 + ssd2, { src1 : [(2, 4), (1, 2), (694, 723)] })
        self.assertEqual(ssd3 + ssd4, { src1 : [(1, 3, "tag1"), (2, 4, "tag2"), (1, 2, "tag3")] })
        self.assertEqual(ssd3 + ssd5, { src1 : [(1, 3, "tag1")], src2 : [(None, 3, "tag4")] })
        self.assertRaises(AssertionError, lambda: ssd1 + ssd3)


    def test_isTagged(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        self.assertEqual(SourceScopeDict(tagged=False).isTagged(), False)
        self.assertEqual(SourceScopeDict(tagged=True).isTagged(),  True)
        self.assertEqual(SourceScopeDict({ src : [(1, 2)] }).isTagged(),        False)
        self.assertEqual(SourceScopeDict({ src : [(1, 2, "tag")] }).isTagged(), True)
        self.assertEqual(SourceScopeDict({ src : [(691, 717)] },        int=True).isTagged(), False)
        self.assertEqual(SourceScopeDict({ src : [(691, 717, "tag")] }, int=True).isTagged(), True)


    def test_insert(self):
        # __add__ use insert
        pass


    def test_matchEach(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        ssd = SourceScopeDict({ src : [(627, 1026)] })
        self.assertEqual(testMapSMD(lambda mres: mres and mres.end(), ssd.matchEach(".*DECLARE")),
                         { dataFilepath("civ", "algorithm2.h") : [642] })

        ssd = SourceScopeDict({ src : [(627, 1026, "tag")] })
        self.assertEqual(testMapSMD(lambda tmres: tmres and (tmres[0].end(), tmres[1]), ssd.matchEach(".*DECLARE")),
                         { dataFilepath("civ", "algorithm2.h") : [(642, "tag")] })

        ssd = SourceScopeDict({ src : [(627, 1026), (3281, 3331), (None, 100)] })
        smd = ssd.matchEach(".*(DEFINE|DECLARE)")
        self.assertEqual(testMapSMD(lambda mres: mres and mres.end(), smd),
                         { dataFilepath("civ", "algorithm2.h") : [642, 3288] })
        self.assertEqual(testMapSMD(lambda mres: mres and mres.end(), smd.missing),
                         { dataFilepath("civ", "algorithm2.h") : [None] })


    def test_isDictTagged(self):
        
        src1 = SourceFile(dataFilepath("civ", "algorithm2.h"))
        src2 = SourceFile(dataFilepath("civ", "CvUnitSort.h"))

        self.assertEqual(SourceScopeDict.isDictTagged(SourceScopeDict({ src1 : [(627, 1026)] })), False)
        self.assertEqual(SourceScopeDict.isDictTagged(SourceScopeDict(tagged=True)), True)
        self.assertEqual(SourceScopeDict.isDictTagged({ src1 : [(627, 1026)] }), False)
        self.assertEqual(SourceScopeDict.isDictTagged({ src1 : [(627, 1026, "tag")] }), True)
        self.assertRaises(AssertionError, SourceScopeDict.isDictTagged, {})
        self.assertRaises(AssertionError, SourceScopeDict.isDictTagged, { src1 : [(627, 1026)], 
                                                                          src2 : [(627, 1026, "tag")] })
        