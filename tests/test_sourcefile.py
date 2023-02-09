from xitools.cppcrawler import SourceFile
from unittest import TestCase
from tstutils import *
import filecmp


class SourceFileTests(TestCase):
    
    maxDiff  = None
    testSuit = "SourceFileTests"


    def setUpClass():
        prepareTmpDir(SourceFileTests.testSuit)
        os.mkdir(tmpFilepath(SourceFileTests.testSuit, "backup"))


    def test_load(self):

        expectedLineJoins = [ 
             690,  716,  799,  803,  875,  903,  907,  975,  979,  994, 1178,
            1216, 1311, 1315, 1392, 1420, 1424, 1492, 1496, 1511, 2568, 2631,
            2715, 2718, 2807, 2890, 2907, 2924, 2928, 2987, 3004, 3088, 3091,
            3173, 3731, 3790, 3870, 3873, 3951, 4030, 4045, 4059, 4063, 4109,
            4135, 4166, 4182, 4191, 4251, 4254, 4309, 6043, 6119, 6163, 6189,
            6193, 6273, 6349, 6395, 6485, 6529, 6558, 6562, 6579, 6671, 6747,
            6811, 6982, 7026, 7061, 7065, 7082, 7101, 7205, 7287, 7369, 7621,
            7665, 7706, 7710, 7727, 7746, 7765, 7840, 7922, 7978, 8004, 8008,
            8094, 8176, 8228, 8318, 8374, 8403, 8407, 8424, 8522, 8604, 8674,
            8845, 8901, 8936, 8940, 8957, 8976, 9086, 9168, 9256, 9508, 9564,
            9605, 9609, 9626, 9645, 9664 ]

        expectedLineJoinsOrg = [ 
             690,   719,   805,   812,   887,   918,   925,   996,  1003,
            1021,  1208,  1249,  1347,  1354,  1434,  1465,  1472,  1543,
            1550,  1568,  2628,  2694,  2781,  2787,  2879,  2965,  2985,
            3005,  3012,  3074,  3094,  3181,  3187,  3272,  3833,  3895,
            3978,  3984,  4065,  4147,  4165,  4182,  4189,  4238,  4267,
            4301,  4320,  4332,  4395,  4401,  4459,  6196,  6275,  6322,
            6351,  6358,  6441,  6520,  6569,  6662,  6709,  6741,  6748,
            6768,  6863,  6942,  7009,  7183,  7230,  7268,  7275,  7295,
            7317,  7424,  7509,  7594,  7849,  7896,  7940,  7947,  7967,
            7989,  8011,  8089,  8174,  8233,  8262,  8269,  8358,  8443,
            8498,  8591,  8650,  8682,  8689,  8709,  8810,  8895,  8968,
            9142,  9201,  9239,  9246,  9266,  9288,  9401,  9486,  9577,
            9832,  9891,  9935,  9942,  9962,  9984, 10006 ]

        expectedClipRanges = [
                  (76, 91, 's'),     (345, 439, 'c'),     (443, 544, 'c'),     (550, 625, 'c'),   (1002, 1109, 'c'), 
              (2017, 2027, 'c'),   (2487, 2509, 'c'),   (4833, 4834, 'c'),   (4838, 4915, 'c'),   (4919, 4925, 'c'), 
              (4929, 4945, 'c'),   (4949, 4958, 'c'),   (4962, 4979, 'c'),   (4983, 4990, 'c'),   (4994, 5050, 'c'), 
              (5054, 5062, 'c'),   (5066, 5075, 'c'),   (5079, 5083, 'c'),   (5087, 5088, 'c'),   (5092, 5116, 'c'), 
              (5120, 5143, 'c'),   (5147, 5148, 'c'),   (5152, 5231, 'c'),   (5235, 5259, 'c'),   (5263, 5327, 'c'), 
              (5331, 5335, 'c'),   (5339, 5392, 'c'),   (5396, 5397, 'c'),   (9692, 9733, 'c'),   (9740, 9750, 'c'), 
            (10428, 10451, 'c'), (10529, 10543, 'c'), (10548, 10573, 'c'), (10578, 10603, 'c'), (10860, 10876, 'c'), 
            (10935, 10955, 'c'), (10960, 10985, 'c'), (10990, 11009, 'c'), (11175, 11198, 'c'), (11335, 11358, 'c'), 
            (11662, 11678, 'c'), (11831, 11852, 'c'), (11972, 11979, 'c'), (12019, 12034, 'c') ]

        expectedLineEnds = [
              14,    16,    40,    64,    66,    94,   142,   190,   239,
             292,   341,   343,   441,   546,   548,   627,   998,  1000,
            1111,  1515,  1517,  1537,  1539,  1604,  1671,  1675,  1704,
            1709,  1711,  1732,  1795,  1799,  1835,  1840,  1842,  1881,
            1968,  1972,  2007,  2012,  2014,  2029,  2075,  2162,  2166,
            2219,  2293,  2309,  2314,  2316,  2354,  2374,  2419,  2423,
            2478,  2482,  2484,  2511,  3177,  3179,  3231,  3287,  3289,
            3339,  3396,  3398,  3451,  3511,  3513,  3570,  3627,  3629,
            3674,  3676,  4313,  4315,  4369,  4427,  4429,  4481,  4540,
            4542,  4597,  4659,  4661,  4720,  4779,  4781,  4824,  4826,
            4829,  4831,  4836,  4917,  4927,  4947,  4960,  4981,  4992,
            5052,  5064,  5077,  5085,  5090,  5118,  5145,  5150,  5233,
            5261,  5329,  5337,  5394,  5399,  5428,  5430,  5477,  5500,
            5504,  5539,  5544,  5546,  5571,  5655,  5659,  5694,  5699,
            5701,  5726,  5809,  5813,  5840,  5845,  5847,  5872,  5976,
            5979,  5981,  6198,  6584,  7106,  7770,  7772,  8013,  8429,
            8981,  9669,  9671,  9689,  9735,  9737,  9752,  9771,  9799,
            9832,  9851,  9872,  9895,  9923,  9943,  9969,  9996, 10020,
           10049, 10070, 10096, 10125, 10149, 10171, 10198, 10228, 10253,
           10275, 10302, 10323, 10349, 10368, 10399, 10425, 10453, 10477,
           10498, 10524, 10526, 10545, 10575, 10605, 10637, 10675, 10707,
           10745, 10765, 10788, 10808, 10834, 10857, 10878, 10932, 10957,
           10987, 11011, 11071, 11108, 11146, 11172, 11200, 11264, 11332,
           11360, 11424, 11492, 11515, 11548, 11587, 11608, 11631, 11657,
           11659, 11680, 11703, 11727, 11758, 11787, 11826, 11828, 11854,
           11879, 11913, 11941, 11967, 11969, 11981, 12005, 12008, 12010,
           12036 ]

        expectedBlockEnds = {
              905: 977,  800:  995, 1422: 1494, 1312: 1512, 1672: 1705, 1796: 1836, 1969: 2008, 2215: 2216, 
            2273: 2290, 2163: 2310, 2420: 2479, 2804: 2805, 2861: 2888, 2716: 2925, 3089: 3174, 3948: 3949, 
            4005: 4028, 3871: 4060, 4252: 4310, 1534: 4826, 5501: 5540, 5656: 5695, 5810: 5841, 5425: 5976, 
            6161: 6191, 6117: 6194, 6392: 6393, 6482: 6483, 6527: 6560, 6347: 6580, 6808: 6809, 6979: 6980, 
            7024: 7063, 6745: 7102, 7366: 7367, 7618: 7619, 7663: 7708, 7285: 7766, 7976: 8006, 7920: 8009, 
            8225: 8226, 8315: 8316, 8372: 8405, 8174: 8425, 8671: 8672, 8842: 8843, 8899: 8938, 8602: 8977, 
            9253: 9254, 9505: 9506, 9562: 9607, 9166: 9665, 9686: 12005 }


        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(src._SourceFile__lineJoins, expectedLineJoins, "Bad line join")
        
        self.assertEqual(src._SourceFile__lineJoinsOrg, expectedLineJoinsOrg, "Bad original line join")
        
        self.assertEqual(src._SourceFile__clipRanges, expectedClipRanges, "Bad clipped range")
        
        self.assertEqual(src._SourceFile__lineEnds, expectedLineEnds, "Bad line end")
        
        self.assertEqual(src._SourceFile__blockEnds, expectedBlockEnds, f"Bad block")
        
        
        src = SourceFile(dataFilepath("civ2", "FAssert.h"))
        src.saveAs(tmpFilepath(self.testSuit, "FAssert.h"), encoding="utf-8")
        self.assertTrue(filecmp.cmp(dataFilepath("civ2", "FAssert.h"), 
                                    tmpFilepath(self.testSuit, "FAssert.h"), False))


    def test_orgPos(self):

        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        self.assertEqual(src.orgPos(0), 0)
        self.assertEqual(src.orgPos(689), 689)
        self.assertEqual(src.orgPos(690), 693)
        self.assertEqual(src.orgPos(1527), 1587)
        self.assertEqual(src.orgPos(2544), 2604)
        self.assertEqual(src.orgPos(12036), 12381)


    def test_intPos(self):

        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        self.assertEqual(src.intPos(0), 0)
        self.assertEqual(src.intPos(689), 689)
        self.assertEqual(src.intPos(693), 690)
        self.assertEqual(src.intPos(692), 690)
        self.assertEqual(src.intPos(691), 690)
        self.assertEqual(src.intPos(690), 690)
        self.assertEqual(src.intPos(1587), 1527)
        self.assertEqual(src.intPos(2604), 2544)
        self.assertEqual(src.intPos(12381), 12036)


    def test_find(self):

        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        self.assertEqual(src.find("detail").start(), 1587)
        self.assertEqual(src.find("detail").end(),   1593)
        self.assertEqual(src.find("detail").group(), "detail")
        self.assertEqual(src.find("fun").start(), 1677)
        self.assertEqual(src.find("fun", skipBlocks=True).start(), 5566)
        self.assertEqual(src.find("fun", skipBlocks=True).group(), "fun")
        self.assertEqual(src.find("return", excludeClips=False).start(), 456)
        self.assertEqual(src.find("return").start(), 931)

        src.setScope(1000, 1100)
        self.assertEqual(src.find("return").start(), 1008)

        src.setScopes([(0, 930), (1000, 1100)])
        self.assertEqual(src.find("return").start(), 1008)

        src.setScopes([(0, 930), (1000, None)])
        self.assertEqual(src.find("return").start(), 1008)
        
        src.setScopes([(1008, None)])
        self.assertEqual(src.find("return").start(), 1008)

        src.setScopes([(None, 937)])
        self.assertEqual(src.find("return").start(), 931)
        
        src.setScopes([(5555, None)])
        self.assertEqual(src.find("struct", skipBlocks=True).start(), 6200)

        src.setScopes([(5579, None)])
        self.assertEqual(src.find("struct", skipBlocks=True).start(), 5631)
        
        src.setScope(None, None)
        self.assertEqual(src.find(r"\w+\s*\([^\{}]*\)\s*\{|\{", excludeClips=False).start(), 599)
        self.assertEqual(src.find(r"\w+\s*\([^\{}]*\)\s*\{|\{").start(), 635)
        

    def test_findUnscoped(self):

        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        self.assertEqual(src.findUnscoped("fun").start(), 1677)
        
        src.setScope(1, 2)
        self.assertEqual(src.findUnscoped("fun").start(), 1677)
        self.assertEqual(src.findUnscoped("fun", 1900).start(), 1957)
        self.assertEqual(src.findUnscoped("fun", 1900, 1901), None)
        self.assertEqual(src.findUnscoped("fun", None, 1700).start(), 1677)
        
        self.assertEqual(src.findUnscoped("fun", skipBlocks=True).start(), 5566)
        self.assertEqual(src.findUnscoped("struct", 5555, skipBlocks=True).start(), 6200)
        self.assertEqual(src.findUnscoped("struct", 5579, skipBlocks=True).start(), 5631)
        
        self.assertEqual(src.findUnscoped("return", excludeClips=False).start(), 456)

        self.assertEqual(src.findUnscoped(r"(?i)FuN", 2560).start(), 2591)
        self.assertEqual(src.findUnscoped(r"(?i)FuN", 2560).group(), "FUN")
        
        self.assertEqual(src.findUnscoped(r"\w+\s*\([^\{}]*\)\s*\{|\{", excludeClips=False).start(), 599)
        self.assertEqual(src.findUnscoped(r"\w+\s*\([^\{}]*\)\s*\{|\{").start(), 635)


    def test_findAll(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        expectedPos = [
            1665, 1793, 1942, 2136, 2698, 3899, 5631, 5725, 5880, 6200, 6445, 6867, 7428, 8093, 8362, 8814, 9405 ]
        self.assertEqual(list(map(lambda mres: mres.start(), 
                                  list(src.findAll("struct")) )), expectedPos)

        expectedPos = [6200, 6445, 6867, 7428, 8093, 8362, 8814, 9405]
        self.assertEqual(list(map(lambda mres: mres.start(), 
                                  list(src.findAll("struct", skipBlocks=True)) )), 
                         expectedPos)

        expectedPos = [5121, 6200, 6445, 6867, 7428, 8093, 8362, 8814, 9405]
        self.assertEqual(list(map(lambda mres: mres.start(), 
                                  list(src.findAll("struct", skipBlocks=True, excludeClips=False)) )), 
                         expectedPos)
        
        expectedPos = [5121, 6200, 6445, 6867]
        src.setScope(1000, 7000)
        self.assertEqual(list(map(lambda mres: mres.start(), 
                                  list(src.findAll("struct", skipBlocks=True, excludeClips=False)) )), 
                         expectedPos)
        
        expectedPos = [1665, 1793, 1942, 2136, 2698, 3899, 5631, 5725, 5880, 6200, 6445, 6867, 8814, 9405]
        src.setScopes([(1000, 7000), (8500, None)])
        self.assertEqual(list(map(lambda mres: mres.start(), 
                                  list(src.findAll("struct")) )), 
                         expectedPos)
        
        src.setScope(None, 1360)
        self.assertEqual([ mres.start() for mres in src.findAll(r"\w+\s*\([^\{}]*\)\s*\{|\{", excludeClips=False) ],
                         [599, 866, 1111])
        self.assertEqual([ mres.start() for mres in src.findAll(r"\w+\s*\([^\{}]*\)\s*\{|\{") ],
                         [635, 866, 1149])
        self.assertEqual([ mres.start() for mres in src.findAll(r"\w+\s*\([^\{}]*\)\s*\{|\{", skipBlocks=True) ],
                         [635, 1149])


    def test_findAllUnscoped(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        expectedPos = [
            1665, 1793, 1942, 2136, 2698, 3899, 5631, 5725, 5880, 6200, 6445, 6867, 7428, 8093, 8362, 8814, 9405 ]
        self.assertEqual(list(map(lambda mres: mres.start(), 
                                  list(src.findAllUnscoped("struct")) )), 
                         expectedPos)
        

        src.setScope(1, 2)


        expectedPos = [
            1665, 1793, 1942, 2136, 2698, 3899, 5631, 5725, 5880, 6200, 6445, 6867, 7428, 8093, 8362, 8814, 9405 ]
        self.assertEqual(list(map(lambda mres: mres.start(), 
                                  list(src.findAllUnscoped("struct")) )), 
                         expectedPos)


        expectedPos = [6200, 6445, 6867, 7428, 8093, 8362, 8814, 9405]
        self.assertEqual(list(map(lambda mres: mres.start(), 
                                  list(src.findAllUnscoped("struct", skipBlocks=True)) )), 
                         expectedPos)

        expectedPos = [5121, 6200, 6445, 6867, 7428, 8093, 8362, 8814, 9405]
        self.assertEqual(list(map(lambda mres: mres.start(), 
                                  list(src.findAllUnscoped("struct", skipBlocks=True, excludeClips=False)) )), 
                         expectedPos)
        
        expectedPos = [5121, 6200, 6445, 6867]
        self.assertEqual(list(map(lambda mres: mres.start(), 
                                  list(src.findAllUnscoped("struct", 1000, 7000, 
                                                               skipBlocks=True, excludeClips=False)) )), 
                         expectedPos)
        
        expectedPos = [8814, 9405]
        self.assertEqual(list(map(lambda mres: mres.start(), 
                                  list(src.findAllUnscoped("struct", 8500)) )), 
                         expectedPos)
        
        self.assertEqual([ mres.start() for mres in src.findAllUnscoped(r"\w+\s*\([^\{}]*\)\s*\{|\{", 
                                                                            excludeClips=False) ][:3],
                         [599, 866, 1111])
        self.assertEqual([ mres.start() for mres in src.findAllUnscoped(r"\w+\s*\([^\{}]*\)\s*\{|\{") ][:3],
                         [635, 866, 1149])
        self.assertEqual([ mres.start() for mres in src.findAllUnscoped(r"\w+\s*\([^\{}]*\)\s*\{|\{", 
                                                                            skipBlocks=True) ][:5],
                         [635, 1149, 1594, 5578, 6273 ])

        
        src = SourceFile(dataFilepath("singles", "CvArtFileMgr.cpp"))

        self.assertEqual(list(src.findAllUnscoped(r"PROFILE", 1763, 2256)), [])


    def test_matchUnscoped(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        self.assertEqual(src.matchUnscoped(r".*once").end(), 12)

        self.assertEqual(src.matchUnscoped(r"(?:.|\n)*#define algorithm2_h__").end(), 62)

        self.assertEqual(src.matchUnscoped(r"(?:.|\n)*#define algorithm2_h__", end=60), None)

        self.assertEqual(src.matchUnscoped(r"namespace\s*(\w+)\s*\{", 5552).end(), 5579)
        self.assertEqual(src.matchUnscoped(r"namespace\s*(\w+)\s*\{", 5552).group(1), "map_fun_details")


    def test_replaceMatches(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        src.replaceMatch(src.find("detail"), "another_detail")
        self.assertEqual(src.intCode()[src.intPos(1587) : src.intPos(1587) + 14], "another_detail")
        

        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        src.replaceMatches(list(src.findAll("namespace ")), "namespace\t")
        
        self.assertEqual(list(map(lambda mres: mres.group(0), src.findAll(r"namespace\s"))), 
                         ["namespace\t"]*3)


        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        src.replaceMatches(list(src.findAll(r"namespace (\w+)\b")), lambda m: f"namespace another_{m.group(1)}")

        self.assertEqual(list(map(lambda mres: mres.group(1), src.findAll(r"namespace\s(\w+)\b"))), 
                         ["another_detail", "another_map_fun_details", "another_algo"])


        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        src.replaceMatches(list(src.findAll(r"return name<O, D, V>\(static_cast<const D&>\(f\), val\); \t\}")),
                           "return name<O, D, V>(static_cast<const D&>(f), val); \t}")

        expectedLineJoins = [ 
             690,   716,   799,   803,   875,   903,   907,   975,   979,   994,  1178,
            1216,  1311,  1315,  1392,  1420,  1424,  1492,  1496,  1511,  2568,  2631,
            2715,  2718,  2807,  2890,  2907,  2924,  2928,  2987,  3004,  3088,  3091,
            3173,  3731,  3790,  3870,  3873,  3951,  4030,  4045,  4059,  4063,  4109,
            4135,  4166,  4182,  4191,  4251,  4254,         6043,  6119,  6163,  6189,
            6193,  6273,  6349,  6395,  6485,  6529,  6558,  6562,  6579,  6671,  6747,
            6811,  6982,  7026,  7061,  7065,  7082,  7101,  7205,  7287,  7369,  7621,
            7665,  7706,  7710,  7727,  7746,  7765,  7840,  7922,  7978,  8004,  8008,
            8094,  8176,  8228,  8318,  8374,  8403,  8407,  8424,  8522,  8604,  8674,
            8845,  8901,  8936,  8940,  8957,  8976,  9086,  9168,  9256,  9508,  9564,
            9605,  9609,  9626,  9645,  9664 ]

        expectedLineJoinsOrg = [ 
             690,   719,   805,   812,   887,   918,   925,   996,  1003,  1021,  1208,
            1249,  1347,  1354,  1434,  1465,  1472,  1543,  1550,  1568,  2628,  2694,
            2781,  2787,  2879,  2965,  2985,  3005,  3012,  3074,  3094,  3181,  3187,
            3272,  3833,  3895,  3978,  3984,  4065,  4147,  4165,  4182,  4189,  4238,
            4267,  4301,  4320,  4332,  4395,  4401,         6193,  6272,  6319,  6348,
            6355,  6438,  6517,  6566,  6659,  6706,  6738,  6745,  6765,  6860,  6939,
            7006,  7180,  7227,  7265,  7272,  7292,  7314,  7421,  7506,  7591,  7846,
            7893,  7937,  7944,  7964,  7986,  8008,  8086,  8171,  8230,  8259,  8266,
            8355,  8440,  8495,  8588,  8647,  8679,  8686,  8706,  8807,  8892,  8965,
            9139,  9198,  9236,  9243,  9263,  9285,  9398,  9483,  9574,  9829,  9888,
            9932,  9939,  9959,  9981,  10003 ]
        
        self.assertEqual(src._SourceFile__lineJoins, expectedLineJoins, "Bad line join after "
                         "replacment of: return name<O, D, V>(static_cast<const D&>(f), val); \t}")
        
        self.assertEqual(src._SourceFile__lineJoinsOrg, expectedLineJoinsOrg, "Bad original line join after "
                         "replacment of: return name<O, D, V>(static_cast<const D&>(f), val); \t}")
        

    def test_replace(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        src.replace("detail", "another_detail")

        self.assertEqual(src.intCode()[src.intPos(1587) : src.intPos(1587) + 14], "another_detail")
        

        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        src.replace("namespace ", "namespace\t")

        self.assertEqual(list(map(lambda mres: mres.group(0), src.findAll(r"namespace\s"))), 
                         ["namespace\t"]*3)


        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        src.replace(r"namespace (\w+)\b", lambda m: f"namespace another_{m.group(1)}")

        self.assertEqual(list(map(lambda mres: mres.group(1), src.findAll(r"namespace\s(\w+)\b"))), 
                         ["another_detail", "another_map_fun_details", "another_algo"])
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        

        src.replace(r"namespace (\w+)\b", lambda m: f"namespace another_{m.group(1)}", 2)

        self.assertEqual(list(map(lambda mres: mres.group(1), src.findAll(r"namespace\s(\w+)\b"))), 
                         ["another_detail", "another_map_fun_details", "algo"])


        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        src.replace(r"return name<O, D, V>\(static_cast<const D&>\(f\), val\); \t\}",
                    "return name<O, D, V>(static_cast<const D&>(f), val); \t}")

        expectedLineJoins = [ 
             690,   716,   799,   803,   875,   903,   907,   975,   979,   994,  1178,
            1216,  1311,  1315,  1392,  1420,  1424,  1492,  1496,  1511,  2568,  2631,
            2715,  2718,  2807,  2890,  2907,  2924,  2928,  2987,  3004,  3088,  3091,
            3173,  3731,  3790,  3870,  3873,  3951,  4030,  4045,  4059,  4063,  4109,
            4135,  4166,  4182,  4191,  4251,  4254,         6043,  6119,  6163,  6189,
            6193,  6273,  6349,  6395,  6485,  6529,  6558,  6562,  6579,  6671,  6747,
            6811,  6982,  7026,  7061,  7065,  7082,  7101,  7205,  7287,  7369,  7621,
            7665,  7706,  7710,  7727,  7746,  7765,  7840,  7922,  7978,  8004,  8008,
            8094,  8176,  8228,  8318,  8374,  8403,  8407,  8424,  8522,  8604,  8674,
            8845,  8901,  8936,  8940,  8957,  8976,  9086,  9168,  9256,  9508,  9564,
            9605,  9609,  9626,  9645,  9664 ]

        expectedLineJoinsOrg = [ 
             690,   719,   805,   812,   887,   918,   925,   996,  1003,  1021,  1208,
            1249,  1347,  1354,  1434,  1465,  1472,  1543,  1550,  1568,  2628,  2694,
            2781,  2787,  2879,  2965,  2985,  3005,  3012,  3074,  3094,  3181,  3187,
            3272,  3833,  3895,  3978,  3984,  4065,  4147,  4165,  4182,  4189,  4238,
            4267,  4301,  4320,  4332,  4395,  4401,         6193,  6272,  6319,  6348,
            6355,  6438,  6517,  6566,  6659,  6706,  6738,  6745,  6765,  6860,  6939,
            7006,  7180,  7227,  7265,  7272,  7292,  7314,  7421,  7506,  7591,  7846,
            7893,  7937,  7944,  7964,  7986,  8008,  8086,  8171,  8230,  8259,  8266,
            8355,  8440,  8495,  8588,  8647,  8679,  8686,  8706,  8807,  8892,  8965,
            9139,  9198,  9236,  9243,  9263,  9285,  9398,  9483,  9574,  9829,  9888,
            9932,  9939,  9959,  9981,  10003 ]
        
        self.assertEqual(src._SourceFile__lineJoins, expectedLineJoins, "Bad line join after "
                         "replacment of: return name<O, D, V>(static_cast<const D&>(f), val); \t}")
        
        self.assertEqual(src._SourceFile__lineJoinsOrg, expectedLineJoinsOrg, "Bad original line join after "
                         "replacment of: return name<O, D, V>(static_cast<const D&>(f), val); \t}")
        

    def test_tryScopeToNamespaceBody(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        src.tryScopeToNamespaceBody("detail")
        self.assertEqual(src._intScopes(), [(src.intPos(1595), src.intPos(4979), "detail")])


        src.resetScopes()

        src.tryScopeToNamespaceBody("map_fun_details|algo")
        self.assertEqual(src._intScopes(), 
                         [(src.intPos(5579), src.intPos(6129), "map_fun_details"), 
                          (src.intPos(10032), src.intPos(12350), "algo")])
        
        
    def test_tryScopeToClassBody(self):
        
        src = SourceFile(dataFilepath("civ", "CvUnitSort.h"))
        
        self.assertTrue(src.tryScopeToClassBody("*", "UnitSortBase"))
        self.assertEqual(src._intScopes(), [(src.intPos(688), src.intPos(1242), ('class', 'UnitSortBase'))])


        src.resetScopes()

        src.tryScopeToClassBody("class", "UnitSortMove")
        self.assertEqual(src._intScopes(), [(src.intPos(1513), src.intPos(1678), ('class', 'UnitSortMove'))])


        src.resetScopes()

        src.tryScopeToClassBody("class", "UnitSortL.*")
        self.assertEqual(src._intScopes(), [(src.intPos(3562), src.intPos(4041), ('class', 'UnitSortList')), 
                                            (src.intPos(4075), src.intPos(4315), ('class', 'UnitSortListWrapper'))])
        

        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        self.assertFalse(src.tryScopeToClassBody("union|class", r"\w+"))
        

    def test_tryScopeToStructBody(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        src.setScope(None, 8019)
        self.assertTrue(src.tryScopeToStructBody(r"\w+"))
        self.assertEqual(src.scopes(), [(6274, 6362, ('struct', 'mem_fn_')), (6519, 6772, ('struct', 'mem_fn_')), 
                                        (6941, 7321, ('struct', 'mem_fn_')), (7508, 8015, ('struct', 'mem_fn_'))])
        
        src.setScope(None, 8019)
        self.assertTrue(src.tryScopeToStructBody(r"\w+", skipBlocks=False))
        res = src.scopes()
        self.assertEqual(res[:2] + res[4:5] + res[9:10], 
                         [(1733, 1765, ('struct', 'algo_functor')), (1857, 1896, ('struct', 'is_algo_functor')), 
                          (2786, 3009, ('struct', 'name')), (6274, 6362, ('struct', 'mem_fn_'))])

        src.setScope(1770, None)
        self.assertTrue(src.tryScopeToStructBody("\w+_functor"))
        self.assertEqual(src.scopes(), [(1857, 1896, ('struct', 'is_algo_functor')), 
                                        (2030, 2068, ('struct', 'is_algo_functor'))])


    def test_saveAs(self):
        
        src1 = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        src1.saveAs(tmpFilepath(self.testSuit, "algo.h"), encoding="utf-8")
        self.assertTrue(filecmp.cmp(dataFilepath("civ", "algorithm2.h"), tmpFilepath(self.testSuit, "algo.h"), False))

        self.assertRaises(FileExistsError, src1.saveAs, tmpFilepath(self.testSuit, "algo.h"))
        
        self.assertRaises(FileExistsError, src1.save)
        

        src2 = SourceFile(dataFilepath("civ", "CvUnitSort.h"))

        self.assertRaises(FileExistsError, src2.saveAs, tmpFilepath(self.testSuit, "algo.h"))
        
        src2.saveAs(tmpFilepath(self.testSuit, "algo.h"), force=True, encoding="utf-8")
        self.assertTrue(filecmp.cmp(dataFilepath("civ", "CvUnitSort.h"), tmpFilepath(self.testSuit, "algo.h"), False))

        src1.save(backupDir=tmpFilepath(self.testSuit, "backup"), force=True, encoding="utf-8")
        self.assertTrue(filecmp.cmp(dataFilepath("civ", "algorithm2.h"), tmpFilepath(self.testSuit, "algo.h"), False))
        self.assertTrue(filecmp.cmp(dataFilepath("civ", "CvUnitSort.h"), tmpFilepath(self.testSuit, "backup/algo.h"), 
                                    False))
        
        self.assertRaises(FileExistsError, src1.save, backupDir=tmpFilepath(self.testSuit, "backup"), force=True)
        # because the backup file already exists


    def test_loadCvGlobals(self):
        
        src = SourceFile(dataFilepath("civ2", "CvGlobals.cpp"))
        src.saveAs(tmpFilepath(self.testSuit, "CvGlobals.cpp"), encoding="utf-8")
        self.assertTrue(filecmp.cmp(dataFilepath("civ2", "CvGlobals.cpp"), 
                                    tmpFilepath(self.testSuit, "CvGlobals.cpp"), False))


    def test_insertBlockSPrefix(self):

        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        src.insertBlockSPrefix("PROFILE();", 1732)
        src.saveAs(tmpFilepath(self.testSuit, "algorithm2_insert_prof1.h"), encoding="utf-8")
        self.assertTrue(filecmp.cmp(dataFilepath("results", "algorithm2_insert_prof1.h"), 
                                    tmpFilepath(self.testSuit, "algorithm2_insert_prof1.h"), False))
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        src.insertBlockSPrefix("PROFILE();", 6320)
        src.saveAs(tmpFilepath(self.testSuit, "algorithm2_insert_prof2.h"), encoding="utf-8")
        self.assertTrue(filecmp.cmp(dataFilepath("results", "algorithm2_insert_prof2.h"), 
                                    tmpFilepath(self.testSuit, "algorithm2_insert_prof2.h"), False))
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        src.insertBlockSPrefix("PROFILE();", 8495)
        src.saveAs(tmpFilepath(self.testSuit, "algorithm2_insert_prof3.h"), encoding="utf-8")
        self.assertTrue(filecmp.cmp(dataFilepath("results", "algorithm2_insert_prof3.h"), 
                                    tmpFilepath(self.testSuit, "algorithm2_insert_prof3.h"), False))

        src = SourceFile(dataFilepath("singles", "algorithm2_mod1.h"))
        src.insertBlockSPrefix("PROFILE();", 2223, skipComments=True)
        src.saveAs(tmpFilepath(self.testSuit, "algorithm2_mod1_insert_prof1.h"), encoding="utf-8")
        self.assertTrue(filecmp.cmp(dataFilepath("results", "algorithm2_mod1_insert_prof1.h"), 
                                    tmpFilepath(self.testSuit, "algorithm2_mod1_insert_prof1.h"), False))

        src = SourceFile(dataFilepath("singles", "algorithm2_mod1.h"))
        src.insertBlockSPrefix("PROFILE();", 2223, skipComments=False)
        src.saveAs(tmpFilepath(self.testSuit, "algorithm2_mod1_insert_prof2.h"), encoding="utf-8")
        self.assertTrue(filecmp.cmp(dataFilepath("results", "algorithm2_mod1_insert_prof2.h"), 
                                    tmpFilepath(self.testSuit, "algorithm2_mod1_insert_prof2.h"), False))

        src = SourceFile(dataFilepath("singles", "algorithm2_mod2.h"))
        src.insertBlockSPrefix("PROFILE();", 2223, skipComments=True)
        src.saveAs(tmpFilepath(self.testSuit, "algorithm2_mod2_insert_prof1.h"), encoding="utf-8")
        self.assertTrue(filecmp.cmp(dataFilepath("results", "algorithm2_mod2_insert_prof1.h"), 
                                    tmpFilepath(self.testSuit, "algorithm2_mod2_insert_prof1.h"), False))

        src = SourceFile(dataFilepath("singles", "algorithm2_mod2.h"))
        src.insertBlockSPrefix("PROFILE();", 2223, skipComments=True)
        src.saveAs(tmpFilepath(self.testSuit, "algorithm2_mod2_insert_prof2.h"), encoding="utf-8")
        self.assertTrue(filecmp.cmp(dataFilepath("results", "algorithm2_mod2_insert_prof2.h"), 
                                    tmpFilepath(self.testSuit, "algorithm2_mod2_insert_prof2.h"), False))
        

    def test_intLocation(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))

        self.assertEqual(src.intLocation(694), (17, 65))
        self.assertEqual(src.intLocation(691, int=True), (17, 65))


    def test_blockEnd(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(src.blockEnd(809), 1025)
        self.assertEqual(src.blockEnd(800, int=True), 1025 - 30)


    def test_isClipped(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertTrue(src.isClipped(80))
        self.assertFalse(src.isClipped(343))
        self.assertTrue(src.isClipped(352))
        self.assertFalse(src.isClipped(1030))

        self.assertTrue(src.isClipped(80, int=True))
        self.assertFalse(src.isClipped(343, int=True))
        self.assertTrue(src.isClipped(1030, int=True))
        
        
    def test_getClipRange(self):
        
        src = SourceFile(dataFilepath("civ", "algorithm2.h"))
        
        self.assertEqual(src.getClipRange(80), (76, 91, 's'))
        self.assertEqual(src.getClipRange(1030), None)

        self.assertEqual(src.getClipRange(80, int=True), (76, 91, 's'))
        self.assertEqual(src.getClipRange(1030, int=True), (1032 - 30, 1139 - 30, 'c'))
