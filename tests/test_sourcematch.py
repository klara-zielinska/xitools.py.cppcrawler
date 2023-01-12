from xitools.cppcrawler import SourceFile, SourceRangeMatch
from unittest import TestCase
from tstutils import *


class SourceRangeMatchTests(TestCase):

    testSuit = "SourceRangeMatchTests"


    def setUpClass():
        prepareTmpDir(SourceRangeMatchTests.testSuit)


    def test_group(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        self.assertEqual(SourceRangeMatch(src, (4469, 4469 + 6)).group(0), "DEFINE")