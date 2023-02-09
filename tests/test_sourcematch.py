from xitools.cppcrawler import SourceFile, SourceRangeMatch
from unittest import TestCase
from tstutils import *


class SourceRegexMatchTests(TestCase):
    
    maxDiff  = None
    testSuit = "SourceRegexMatchTests"


    def setUpClass():
        prepareTmpDir(SourceRegexMatchTests.testSuit)


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


    def test_group(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).group(0), "DEFINE")
        

    def test_start(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).start(0), 4469)

    def test_end(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).end(0), 4469 + 6)
        

    def test_intStart(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).intStart(0), 4316)
        

    def test_intEnd(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).intEnd(0), 4322)


    def test_groups(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).groups(), ())

        
    def test_startLoc(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).startLoc(0), (128, 2))

        
    def test_endLoc(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).endLoc(0), (128, 8))
