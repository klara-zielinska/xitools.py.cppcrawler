from xitools.cppcrawler import SourceFile, SourceRangeMatch
from unittest import TestCase
from tstutils import *


class SourceRegexMatchTests(TestCase):
    
    maxDiff  = None
    testSuit = "SourceRegexMatchTests"


    def setUpClass():
        prepareTmpDir(SourceRegexMatchTests.testSuit)
        

    def test___getitem__(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        mres = src.find(r"using (\w+)::(\w+)")

        self.assertEqual(mres[0], "using bst::copy")
        self.assertEqual(mres[1], "bst")
        self.assertEqual(mres[2], "copy")
        

    def test___str__(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(str(src.find(r"using \w+::\w+::\w+")), 
                         "<xitools.cppcrawler.SourceRegexMatch object; "
                         "start=(269, 2), end=(269, 31) match='using bst::algorithm::copy_if'>")


    def test_groupdict(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        mres = src.find(r"using (\w+)::(?P<mid>\w+)::(?P<last>\w+)")
        self.assertEqual(mres.groupdict(), { "mid" : "algorithm", "last" : "copy_if" })
        
        mres = src.find(r"using(?P<weird>gwf928)? (\w+)::(?P<mid>\w+)::(?P<last>\w+)")
        self.assertEqual(mres.groupdict(), { "weird" : None, "mid" : "algorithm", "last" : "copy_if" })
        
        mres = src.find(r"using(?P<weird>gwf928)? (\w+)::(?P<mid>\w+)::(?P<last>\w+)")
        self.assertEqual(mres.groupdict(default=-1), { "weird" : -1, "mid" : "algorithm", "last" : "copy_if" })


    def test_groups(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        mres = src.find(r"using (\w+)::(?P<mid>\w+)::(\w+)")
        self.assertEqual(mres.groups(), ("bst", "algorithm", "copy_if"))
        
        mres = src.find(r"using(?P<weird>gwf928)? (\w+)::(?P<mid>\w+)::(?P<last>\w+)")
        self.assertEqual(mres.groups(), (None, "bst", "algorithm", "copy_if"))
        
        mres = src.find(r"using(?P<weird>gwf928)? (\w+)::(?P<mid>\w+)::(?P<last>\w+)")
        self.assertEqual(mres.groups(default=-1), (-1, "bst", "algorithm", "copy_if"))


    def test_captures(self):

        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        self.assertEqual(src.find(r"using (?P<a>\w+)::(?P<a>\w+)").captures(1), ["bst", "copy"])


    def test_starts(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        mres = src.find(r"using (?P<a>\w+)::(?P<a>\w+)")
        self.assertEqual(mres.starts(1), [10104, 10109])
        

    def test_ends(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        mres = src.find(r"using (?P<a>\w+)::(?P<a>\w+)")
        self.assertEqual(mres.ends(1), [10107, 10113])


    def test_group(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        mres = src.find(r"using (\w+)::(\w+)")
        self.assertEqual(mres.group(0), "using bst::copy")
        self.assertEqual(mres.group(1), "bst")
        self.assertEqual(mres.group(2), "copy")

        self.assertEqual(mres.group(0, 2, 1), ("using bst::copy", "copy", "bst"))
        

    def test_start(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        mres = src.find(r"using (\w+)::(\w+)")
        self.assertEqual(mres.start(0), 10098)
        self.assertEqual(mres.start(1), 10104)
        self.assertEqual(mres.start(2), 10109)

        self.assertEqual(mres.start(0, 2, 1), (10098, 10109, 10104))
        

    def test_end(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        mres = src.find(r"using (\w+)::(\w+)")
        self.assertEqual(mres.end(0), 10113)
        self.assertEqual(mres.end(1), 10107)
        self.assertEqual(mres.end(2), 10113)

        self.assertEqual(mres.end(0, 2, 1), (10113, 10113, 10107))
        

    def test_intStart(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        mres = src.find(r"using (\w+)::(\w+)")
        self.assertEqual(mres.intStart(0), 9753)
        self.assertEqual(mres.intStart(1), 9759)
        self.assertEqual(mres.intStart(2), 9764)

        self.assertEqual(mres.intStart(0, 2, 1), (9753, 9764, 9759))
        

    def test_intEnd(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        mres = src.find(r"using (\w+)::(\w+)")
        self.assertEqual(mres.intEnd(0), 9768)
        self.assertEqual(mres.intEnd(1), 9762)
        self.assertEqual(mres.intEnd(2), 9768)

        self.assertEqual(mres.intEnd(0, 2, 1), (9768, 9768, 9762))

        
    def test_startLoc(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        mres = src.find(r"using (\w+)::(?P<mid>\w+)::(\w+)")
        self.assertEqual(mres.startLoc(),  (269, 2))
        self.assertEqual(mres.startLoc(1), (269, 8))
        self.assertEqual(mres.startLoc("mid"), (269, 13))
        self.assertEqual(mres.startLoc(3), (269, 24))

        
    def test_endLoc(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        mres = src.find(r"using (\w+)::(?P<mid>\w+)::(\w+)")
        self.assertEqual(mres.endLoc(),  (269, 31))
        self.assertEqual(mres.endLoc(1), (269, 11))
        self.assertEqual(mres.endLoc("mid"), (269, 22))
        self.assertEqual(mres.endLoc(3), (269, 31))



class SourceRangeMatchTests(TestCase):

    testSuit = "SourceRangeMatchTests"


    def setUpClass():
        prepareTmpDir(SourceRangeMatchTests.testSuit)


    def test_groupdict(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).groupdict(), {})


    def test_group(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).group(0), "DEFINE")
        self.assertEqual(SourceRangeMatch(src, [(0, 12), (0, 1)]).group(1), "#")
        

    def test_start(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).start(0), 4469)

    def test_end(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).end(0), 4469 + 6)
        

    def test_intStart(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).intStart(0), 4316)
        self.assertEqual(SourceRangeMatch(src, [(0, 12), (1, 1)]).intStart(0, 1), (0, 1))
        

    def test_intEnd(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).intEnd(0), 4322)
        self.assertEqual(SourceRangeMatch(src, [(0, 12), (1, 1)]).intEnd(0, 1), (12, 1))


    def test_groups(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).groups(), ())
        self.assertEqual(SourceRangeMatch(src, [(0, 12)]).groups(), ())
        self.assertEqual(SourceRangeMatch(src, [(0, 12), (0, 1)]).groups(), ("#",))


    def test_captures(self):

        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, [(0, 12), (0, 1)]).captures(1), ["#"])


    def test_starts(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, [(0, 12), (0, 1)]).starts(1), [0])
        

    def test_ends(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, [(0, 12), (0, 1)]).ends(1), [1])

        
    def test_startLoc(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).startLoc(0), (128, 2))

        
    def test_endLoc(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).endLoc(0), (128, 8))


    def test___lt__(self):

        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertFalse(SourceRangeMatch(src, (10, 20)) < None)
        self.assertFalse(SourceRangeMatch(src, (10, 20)) < SourceRangeMatch(src, (10, 20)))
        self.assertTrue(SourceRangeMatch(src,  (10, 20)) < SourceRangeMatch(src, (11, 20)))
        self.assertTrue(SourceRangeMatch(src,  (10, 20)) < SourceRangeMatch(src, (10, 21)))


    def test___eq__(self):

        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertFalse(SourceRangeMatch(src, (10, 20)) == None)
        self.assertFalse(SourceRangeMatch(src, (10, 20)) == SourceRangeMatch(src, (11, 20)))
        self.assertFalse(SourceRangeMatch(src, (10, 20)) == SourceRangeMatch(src, (10, 21)))
        self.assertTrue(SourceRangeMatch(src, (10, 20)) == SourceRangeMatch(src, (10, 20)))
        

    def test___str__(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(str(SourceRangeMatch(src, (0, 12))),
                         "<xitools.cppcrawler.SourceRangeMatch object; "
                         "start=(1, 1), end=(1, 13) match='#pragma once'>")