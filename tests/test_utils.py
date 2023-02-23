from xitools.cppcrawler.utils import *
from unittest import TestCase
from tstutils import *
import xitools.cppcrawler.syntax as synt


class UtilsTests(TestCase):
    
    maxDiff  = None
    testSuit = "UtilsTests"


    def setUpClass():
        prepareTmpDir(UtilsTests.testSuit)


    def test_flatten(self):
        self.assertEqual(flatten([]), [])
        self.assertEqual(flatten([[1, 2], [], [3]]), [1, 2, 3])


    def test_maxCommonPrefix(self):
        self.assertEqual(maxCommonPrefix("aa"), "aa")
        self.assertEqual(maxCommonPrefix("a", "aa"), "a")
        self.assertEqual(maxCommonPrefix("a", "ba"), "")
        self.assertEqual(maxCommonPrefix("aaa", "aaaa", "aaaaaaaa", "aab"), "aa")


    def test_insertRangeSorted(self):
        inputOutput = [
            ([],           None, None, [(None, None)]),
            ([(10, 20)],   None, None, [(None, None)]),
            ([(None, 20)], None, None, [(None, None)]),
            ([(20, None)], None, None, [(None, None)]),
            ([(20, None)], None,   20, [(None, None)]),
            ([(20, 30)],   None,   20, [(None, 30)]),
            ([(25, 30)],   None,   20, [(None, 20), (25, 30)]),
            ([(20, None)],   20,   40, [(20, None)]),
            ([(20, 50)],     20,   40, [(20, 50)]),
            ([(15, 30)],     20,   40, [(15, 40)]),
            ([(15, 30)],     20, None, [(15, None)]),
            ([(20, 30)],      1,    2, [(1, 2), (20, 30)]),
            ([(20, 30)],    100,  120, [(20, 30), (100, 120)]),

            ([(15, 30), (35, 45)], 20, 35, [(15, 45)]),
            ]
            
        for (ranges, start, end, expOut) in inputOutput:
            insertRangeSorted(ranges, start, end)
            self.assertEqual(ranges, expOut)
