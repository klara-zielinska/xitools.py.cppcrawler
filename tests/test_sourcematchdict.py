from xitools.cppcrawler import SourceFile, SourceRangeMatch, SourceMatchDict
from unittest import TestCase
from tstutils import *


class SourceMatchDictTests(TestCase):
    
    maxDiff  = None
    testSuit = "SourceMatchDictTests"


    def setUpClass():
        prepareTmpDir(SourceMatchDictTests.testSuit)


    def test___init__(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        match1 = SourceRangeMatch(src, (627, 634))
        match2 = SourceRangeMatch(src, (0, 7))

        self.assertRaises(AssertionError, SourceMatchDict)

        self.assertEqual(SourceMatchDict(tagged=False), {})
        self.assertEqual(SourceMatchDict(tagged=True),  {})
        self.assertEqual(SourceMatchDict({ src : [match1] }, tagged=False), { src : [match1] })
        self.assertEqual(SourceMatchDict({ src : [(match1, "tag")] }, tagged=True),  { src : [(match1, "tag")] })
        
        self.assertRaises(AssertionError, SourceMatchDict)
        self.assertRaises(AssertionError, SourceMatchDict, { src : [match1] },          tagged=True)
        self.assertRaises(AssertionError, SourceMatchDict, { src : [(match1, "tag")] }, tagged=False)
        self.assertRaises(AssertionError, SourceMatchDict, { src : [match1, (match2, "tag")] }, tagged=False)
        self.assertRaises(AssertionError, SourceMatchDict, { src : [match1, (match2, "tag")] }, tagged=True)
        self.assertRaises(AssertionError, SourceMatchDict, { src : [match1, (match2, "tag")] })
        
        smd = SourceMatchDict({ src : [match1, match2] })
        self.assertEqual(dict(smd), { src : [match2, match1] })
        self.assertEqual(smd.isTagged(), False)

        smd = SourceMatchDict({ src : [(match1, "a"), (match2, "b")] })
        self.assertEqual(dict(smd), { src : [(match2, "b"), (match1, "a")] })
        self.assertEqual(smd.isTagged(), True)


    def test___add__(self):
        
        src1 = SourceFile(dataFilepath("civ", "algorithm2.h"))
        src2 = SourceFile(dataFilepath("civ", "CvUnitSort.h"))

        match1 = SourceRangeMatch(src1, (627, 634))
        match2 = SourceRangeMatch(src1, (0, 7))
        match3 = src2.find("class");

        self.assertEqual(SourceMatchDict({ src1 : [match1] }) +  SourceMatchDict({ src1 : [match2] }),
                         { src1 : [match2, match1]})
        self.assertEqual(SourceMatchDict({ src1 : [match1] }) + SourceMatchDict({ src2 : [match3] }),
                         { src1 : [match1], src2 : [match3] })


    def test_isTagged(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        match1 = SourceRangeMatch(src, (627, 634))
        
        self.assertEqual(SourceMatchDict(tagged=False).isTagged(), False)
        self.assertEqual(SourceMatchDict(tagged=True).isTagged(),  True)
                
        smd = SourceMatchDict({ src : [match1] })
        self.assertEqual(smd.isTagged(), False)

        smd = SourceMatchDict({ src : [(match1, "a")] })
        self.assertEqual(smd.isTagged(), True)
        

    def test_sourceDir(self):
        
        self.assertEqual(os.path.relpath(SourceMatchDict(tagged=False, sourceDir="data/mash").sourceDir()), 
                         os.path.normpath("data/mash"))


    def test_insert(self):
        
        src1 = SourceFile(dataFilepath("civ", "algorithm2.h"))
        src2 = SourceFile(dataFilepath("civ", "CvUnitSort.h"))
        
        match1 = SourceRangeMatch(src1, (627, 634))
        match2 = SourceRangeMatch(src1, (0, 7))
        match3 = src2.find("class");
        
        smd = SourceMatchDict(tagged=True)

        smd.insert(src1, (match1, "tag1"))
        smd.insert(src1, (match2, "tag2"))
        smd.insert(src2, (match3, "tag3"))
        
        self.assertEqual(dict(smd), { src1 : [(match2, "tag2"), (match1, "tag1")], src2 : [(match3, "tag3")] })
        
        self.assertRaises(AssertionError, smd.insert, src1, match1)

        
    def test_filter(self):
        
        src1 = SourceFile(dataFilepath("civ", "algorithm2.h"))
        src2 = SourceFile(dataFilepath("civ", "CvUnitSort.h"))
        
        match1 = SourceRangeMatch(src1, (627, 634))
        match2 = SourceRangeMatch(src1, (0, 7))
        match3 = src2.find("class");
        smd1 = SourceMatchDict({ src1 : [(match2, "tag2"), (match1, "tag1")], src2 : [(match3, "tag3")] })

        smd2 = smd1.filter(lambda src, tmatch: tmatch[1] != "tag2")
        self.assertEqual(dict(smd2), { src1 : [(match1, "tag1")], src2 : [(match3, "tag3")] })
        self.assertTrue(smd1 is smd2)
        
        smd3 = smd1.filter(lambda src, tmatch: tmatch[1] != "tag2", new=True)
        self.assertEqual(dict(smd3), { src1 : [(match1, "tag1")], src2 : [(match3, "tag3")] })
        self.assertTrue(smd1 is not smd3)


    def test_filterPrecededWith(self):
        
        src1 = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        match1 = SourceRangeMatch(src1, (627, 634))
        match2 = SourceRangeMatch(src1, (0, 7))
        match3 = SourceRangeMatch(src1, (1587, 1593))
        
        smd1 = SourceMatchDict({ src1 : [match1, match2, match3] })
        
        smd2 = smd1.filterPrecededWith(r"^|\n")
        self.assertEqual(dict(smd2), { src1 : [match2, match1] })
        self.assertTrue(smd1 is smd2)
        
        smd3 = smd1.filterPrecededWith(r"^|\n", new=True)
        self.assertEqual(dict(smd3), { src1 : [match2, match1] })
        self.assertTrue(smd1 is not smd3)
        
        
    def test_filterNotPrecededWith(self):
        
        src1 = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        match1 = SourceRangeMatch(src1, (627, 634))
        match2 = SourceRangeMatch(src1, (0, 7))
        match3 = SourceRangeMatch(src1, (1587, 1593))
        
        smd1 = SourceMatchDict({ src1 : [match1, match2, match3] })
        
        smd2 = smd1.filterNotPrecededWith(r"^|\n")
        self.assertEqual(dict(smd2), { src1 : [match3] })
        self.assertTrue(smd1 is smd2)
        
        smd3 = smd1.filterNotPrecededWith(r"^|\n", new=True)
        self.assertEqual(dict(smd3), { src1 : [match3] })
        self.assertTrue(smd1 is not smd3)


    def test_scopesBehind(self):
        
        src1 = SourceFile(dataFilepath("civ", "algorithm2.h"))
        src2 = SourceFile(dataFilepath("civ", "CvUnitSort.h"))
        
        match1 = SourceRangeMatch(src1, (627, 634))
        match2 = SourceRangeMatch(src1, (0, 7))
        match3 = SourceRangeMatch(src2, (0, 8));
        
        self.assertEqual(SourceMatchDict({ src1 : [match1, match2], src2 : [match3] }).scopesBehind(),
                         { src1 : [(7, None), (634, None)], src2 : [(8, None)] })
        
        self.assertEqual(SourceMatchDict({ src1 : [(match1, 1), (match2, 2)], src2 : [(match3, 3)] }).scopesBehind(),
                         { src1 : [(7, None, 2), (634, None, 1)], src2 : [(8, None, 3)] })


    def test_getSource(self):
        
        src1 = SourceFile(dataFilepath("civ", "algorithm2.h"))
        src2 = SourceFile(dataFilepath("civ", "CvUnitSort.h"))
        
        match1 = SourceRangeMatch(src1, (627, 634))
        match2 = SourceRangeMatch(src2, (0, 8));

        smd = SourceMatchDict({ src1 : [match1], src2 : [match2] }, sourceDir=dataFilepath("civ"))
        self.assertEqual(smd.getSource(dataFilepath("civ", "algorithm2.h")), src1)
        self.assertEqual(smd.getSource("CvUnitSort.h"), src2)
        
        smd = SourceMatchDict({ src1 : [match1], src2 : [match2] })
        self.assertEqual(smd.getSource(dataFilepath("civ", "algorithm2.h")), src1)


    def test_isDictTagged(self):
        
        src1 = SourceFile(dataFilepath("civ", "algorithm2.h"))
        src2 = SourceFile(dataFilepath("civ", "CvUnitSort.h"))
        
        match1 = SourceRangeMatch(src1, (627, 634))
        match2 = SourceRangeMatch(src2, (0, 8));

        self.assertEqual(SourceMatchDict.isDictTagged(SourceMatchDict({ src1 : [match1] })), False)
        self.assertEqual(SourceMatchDict.isDictTagged(SourceMatchDict(tagged=True)), True)
        self.assertEqual(SourceMatchDict.isDictTagged({ src1 : [match1] }), False)
        self.assertEqual(SourceMatchDict.isDictTagged({ src1 : [(match1, "tag")] }), True)
        self.assertRaises(AssertionError, SourceMatchDict.isDictTagged, {})
        self.assertRaises(AssertionError, SourceMatchDict.isDictTagged, { src1 : [match1], 
                                                                          src2 : [(match2, "tag")] })
        