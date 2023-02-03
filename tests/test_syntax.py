from xitools.cppcrawler import Syntax
from unittest import TestCase
from tstutils import *
import xitools.cppcrawler.syntax as synt


class SyntaxTests(TestCase):
    
    maxDiff  = None
    testSuit = "SyntaxTests"


    def setUpClass():
        prepareTmpDir(SyntaxTests.testSuit)


    def test_addIndent(self):
        self.assertEqual(Syntax.addIndent("l1\r\nllllll2\r\n\r\nl3", "    "), 
                         "    l1\r\n    llllll2\r\n    \r\n    l3")


    def test_makeBaseProtRe(self):
        self.assertEqual(Syntax.makeBaseProtRe("const`CvPlayer*", True), "\s*const\s+CvPlayer\s*\*")
        self.assertEqual(Syntax.makeBaseProtRe("const`CvPlayer*", False, True), "const\s+CvPlayer\s*\*\s*")


    def test_makeTypeRe(self):
        self.assertEqual(Syntax.makeTypeRe("int"), "int")
        self.assertEqual(Syntax.makeTypeRe("unsigned`int"), "unsigned\s+int")
        self.assertEqual(Syntax.makeTypeRe("std::vector<std::pair<int,`bool>`>"), 
                         "std\s*::\s*vector\s*<\s*std\s*::\s*pair\s*<\s*int\s*,\s*bool\s*>\s*>")


    def test_makeMethProtRe(self):
        self.assertEqual(
            Syntax.makeMethProtRe("UnitSortMove::getUnitValue(const`CvPlayer*, const`CvCity*, UnitTypes) const"),
            r"UnitSortMove\s*::\s*getUnitValue\s*\(\s*"
                r"const\s+CvPlayer\s*\*\s*\b(?P<argname>\w*)(?:\s*=\s*"f"(?:{synt._optValRe}))?\s*,\s*"
                r"const\s+CvCity\s*\*\s*\b(?P<argname>\w*)(?:\s*=\s*"f"(?:{synt._optValRe}))?\s*,\s*"
                r"UnitTypes\s*\b(?P<argname>\w*)(?:\s*=\s*"f"(?:{synt._optValRe}))?"
            r"\s*\)\s*const")
        self.assertEqual(
            Syntax.makeMethProtRe("getUnitValue(std::pair<const`CvPlayer*,`const`CvCity*>)"),
            r"getUnitValue\s*\(\s*std\s*::\s*pair\s*<\s*"
                r"const\s+CvPlayer\s*\*\s*,\s*"
                r"const\s+CvCity\s*\*\s*>\s*"
                r"\b(?P<argname>\w*)(?:\s*=\s*"f"(?:{synt._optValRe}))?"
            r"\s*\)")


    def test_parseTempArgsProt(self):
        inputOutput = [ 
            (s:="<>",    ("<>", len(s))),
            (s:="<int>", ("<int>", len(s))),
            (s:="<unsigned   int>", ("<unsigned`int>", len(s))),
            (s:="< unsigned   int,    long>", ("<unsigned`int,`long>", len(s))),
            (s:="< unsigned   int,    long, unsigned\tshort>", ("<unsigned`int,`long,`unsigned`short>", len(s))), 
            (s:="< std::vector < int, Alloc > >", ("<std::vector<int,`Alloc>`>", len(s))),
            (s:="< std::vector < int, Alloc > >; xxx", ("<std::vector<int,`Alloc>`>", s.index(";"))),
            (s:="< std::vector < int, Alloc > >  ; xxx", ("<std::vector<int,`Alloc>`>", s.index(";") - 2))
            ]

        for input, expRes in inputOutput:
            self.assertEqual(Syntax.parseTempArgs(input), expRes)


    def test_parseTypeProt(self):
        inputOutput = [ 
            (s:="int", ("int", len(s))),
            (s:="const int",   ("const`int", len(s))),
            (s:="const unsigned int", ("const`unsigned`int", len(s))),
            (s:="typename const unsigned int", ("typename`const`unsigned`int", len(s))),
                        
            (s:="const * int", ("const*int", len(s))),
            (s:="const long long&", ("const`long`long&", len(s))),
            (s:="const long long  typename&", ("const`long`long`typename&", len(s))),

            (s:="int[10]", ("int[10]", len(s))),
            (s:="int  [   10 + 20 * (30)  ]", ("int[10+20*(30)]", len(s))),

            (s:="A::B", ("A::B", len(s))),
            (s:="A :: B::    C", ("A::B::C", len(s))),
            (s:="A :: B::    C * const *", ("A::B::C*const*", len(s))),

            (s:="vector<int>", ("vector<int>", len(s))),
            (s:="vector  <  int  >", ("vector<int>", len(s))),
            (s:="vector  <  int, Alloc  >", ("vector<int,`Alloc>", len(s))),

            (s:="std::vector< std::vector < int, Alloc > >", 
                ("std::vector<std::vector<int,`Alloc>`>", len(s))),
            (s:="std::vector< std::vector < int, Alloc > > :: iterator", 
                ("std::vector<std::vector<int,`Alloc>`>::iterator", len(s))),
            (s:="std::vector< std::vector < int, Alloc > > :: iterator * const * const&", 
                ("std::vector<std::vector<int,`Alloc>`>::iterator*const*const&", len(s)))
            ]

        for input, expRes in inputOutput:
            self.assertEqual(Syntax.parseType(input), expRes, f"Input: {input}")


    def test_parseExpr(self):
        inputOutput = [ 
            (s:="x", ("x", len(s))),
            (s:="foo()", ("foo()", len(s))),
            (s:="x  ",   ("x", 1)),
            (s:="x  ,",  ("x", 1)),
            (s:="x(1, 2)  ,",  ("x(1, 2)", len(s)-3)),
            (s:="x[1, 2)  ,",  None),
            (s:="x[f(std::max(2, y))]  ,",  ("x[f(std::max(2, y))]", len(s)-3)),
            ]

        for input, expRes in inputOutput:
            self.assertEqual(Syntax.parseExpr(input), expRes, f"Input: {input}")


    def test_parseMethPrototype(self):
        inputOutput = [ 
            (s:="foo()", ("foo()", [], len(s))),
            (s:="foo(unsigned    char  )", ("foo(unsigned`char)", [None], len(s))),
            (s:="foo(int i)", ("foo(int)", ["i"], len(s))),
            (s:="foo(  int i  )   const", ("foo(int) const", ["i"], len(s))),
            (s:="foo(  int i, char* str  )   const", ("foo(int, char*) const", ["i", "str"], len(s))),
            (s:="ClassA::foo(  int i, char * const str  )", ("ClassA::foo(int, char*const)", ["i", "str"], len(s))),
            (s:="ClassA::foo(int &i, long  long  )", ("ClassA::foo(int&, long`long)", ["i", None], len(s))),
            (s:="ClassA:: ~ ClassA(long int )", ("ClassA::~ClassA(long`int)", [None], len(s))),

            (s:="ClassA  ::  f(std::vector< int, std::Alloc >, int i, char * const str  )", 
                ("ClassA::f(std::vector<int,`std::Alloc>, int, char*const)", [None, "i", "str"], len(s))),
            (s:="ClassA  ::  f(std::vector< int, std::Alloc > vec, int i, char * const str  )", 
                ("ClassA::f(std::vector<int,`std::Alloc>, int, char*const)", ["vec", "i", "str"], len(s))),
                
            (s:="CvCity::getProductionPerTurn(ProductionCalc::flags flags = ProductionCalc::Yield) const",
                ("CvCity::getProductionPerTurn(ProductionCalc::flags) const", ["flags"], len(s))),
                
            (s:="CvCity::getProductionPerTurn(ProductionCalc::flags flags = ProductionCalc::Yield, int i) const",
                ("CvCity::getProductionPerTurn(ProductionCalc::flags, int) const", ["flags", "i"], len(s))),

            (s:="foo()  {}", ("foo()", [], 5)),
            (s:="foo() const {}", ("foo() const", [], s.index("{") - 1)),
            ]

        for input, expRes in inputOutput:
            self.assertEqual(Syntax.parseMethPrototype(input), expRes, f"Input: {input}")