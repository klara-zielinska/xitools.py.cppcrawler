from .utils import *
import regex

_escCharsRe = r"[-#$&()*+.?\[\]^{|}~\\]"

_commentRe  = r"//.*|/\*(?:[^\*]|\*[^/])*\*/"
_commentPat = regex.compile(_commentRe)
_stringRe   = r'"(?:[^"\\\n]|\\.)*"'
_stringPat  = regex.compile(_stringRe)
_charRe     = r"'(?:[^'\\\n]|\\.)*'"
_charPat    = regex.compile(_charRe)
_clipRe     = f"{_commentRe}|{_stringRe}|{_charRe}"
_clipPat    = regex.compile(_clipRe)
_idRe = r"\b\w+\b"
__  = f"(?:\\s|{_commentRe})"
___ = f"{__}*+"
_optValRe   = f"{_stringRe}|{_charRe}"r"|[-+]?[\w.]+" # expression should match constants and may accept more
_optValPat  = regex.compile(_optValRe)
_cSymbRe = (r">>=|<<=|<=>|->\*|"
            r"\+=|-=|\*=|/=|%=|\^=|&=|\|=|<<|>>|==|!=|<=|>=|&&|\|\||\+\+|--|->|::|"
            r'''(?<!\*)/(?![/*])|[-+*%^&|~!=<>,\[\]():?'"]''')
_cSymbPat = regex.compile(_cSymbRe)

_opSym0Re = r"\({___}\)|\[{___}]"r"|[-+*/%^&|~!=<>,]{1,3}"
_ptrArgOps0Re = r"(?:\s*[&*]\s*|\s*const\b\s*)+"


# Warning: can find an expression or an initializer
_methFinderRe = (f"(?:{_idRe}{___}::{___})?"
                 r"(?:~|\boperator\b"f"|{_idRe}(?:{___}<(?:{_clipRe}|[^;{{}}])*+>)?){___}"r"\(")

_clipBeginPat   = regex.compile(r"['\"]|//|/\*|\r\n")
_endCharPat     = regex.compile(r"'|\r\n|$")
_endStrPat      = regex.compile(r'"|\r\n|$')
_endComment1Pat = regex.compile(r'\r\n|$')
_endCommentNOrNlPat = regex.compile(r'\*/|\r\n|$')

# no function types support
_methProtAPat = regex.compile(r"(?P<hd>(?:[^(]|\(`)++\()"
                              r"(?:(?P<targ1>{tp})(?:, (?P<targ2>{tp}))*+)?"
                              r"\)(?: (?P<mod>\w++))*".format(tp = r"(?:[^),]|[),]`)++"))
_methProtPat = regex.compile(r"(?:(?P<cont>\w+)::)?(?P<name>operator\(\)|~?[^(]+)(?P<tempArgs><[^(]*>)?"
                             r"\((?P<targ1>{tp})?(?:, (?P<targ2>{tp}))*\)(?P<const> const)?".format(tp = "[^),]+"))
_methProt0Pat = regex.compile(r"(?:(?P<cont>\w+)::)?")
_methProt1Pat = regex.compile(r"(?:(?P<cont>\w+)::)?+(?:~)?+(?P<name>[^(]+)\(")
_methDec0Pat = regex.compile(r"(?<!(?:,)\s*)(?:\b(?P<cont>\w+)\s*::\s*)?(?P<dest>~\s*)?"
                             r"\b(?:operator\b\s*(?P<op>"f"(?:{_opSym0Re})?)"
                                r"|(?P<name>\w+)\s*(?=(?P<x>\(|<)))")
_methDec0aPat = regex.compile(f"\\({___}")
_methDec1Pat = regex.compile(f"{___}"
                             r"(?:\((?P<ptr>"f"{_ptrArgOps0Re}"r")(?P<name>\w+)?"f"{___}"r"\)"
                                 r"|(?P<name>\w+)?)"
                             f"{___}(?=(?P<fn>\())?")
_methDec1aPat = regex.compile(f"{___}(?P<opt>=){___}")
_methDec2Pat = regex.compile(f"{___},?{___}")
_methDec3Pat = regex.compile(f"\\)({___}const)?")
_tpOps0Pat = regex.compile(r"\s*((?:[\*&]|const\b|typename\b|\s+)*)")
_tpOps1Pat = regex.compile(r"(?:[\*&]|const\b|\s+)*(?<!\s)")
_tpSpaceRepPat = regex.compile(r"(\b\s+\b)|\s+")
_tpBuiltInPat = regex.compile(r"(?:unsigned\s+)?(?:(?:short|long(?:\s+long)?)(?:\s+int)?|int|char)")
_tpName0Pat = regex.compile(r"\s*(\w+)")
_tpName1Pat = regex.compile(r"\s*::\s*(\w+)")
_tpArrPat = regex.compile(r"\s*\[[^]]*]")
_tpTailPat = regex.compile(r"(?:\s*typename)?")
_tpFuncPat = regex.compile(r"\s*(?:\((?P<ptr>"f"{_ptrArgOps0Re}"r")\)\s*)?(?=\()")
_tempArgs0Pat = regex.compile(r"\s*<\s*")
_tempArgs1Pat = regex.compile(r"\s*,\s*")
_tempArgs2Pat = regex.compile(r"\s*>")
_lineStartPat = regex.compile(r"^|\r\n")
_indentPat = regex.compile(r"(?<=^|\r\n)[ \t]*")
_expr0Pat = regex.compile(r"\s*+[^\(\)\[\],]+(?P<popen>\(|\[)?(?<!\s)")
_expr1Pat = regex.compile(r"\s*,?\s*")
_expr2Pat = regex.compile(r"[\)\]]")
_classStructHead0Re = r"\b({keyword})\s+({name})\b\s*"
_classStructHead1Pat = regex.compile(r"\s*(?::(?!:)(?:[^;\{]|"f"{_commentRe}"r")*+)?(?=\{)")
_tpProtSymbPat = regex.compile(r"::|[<>*&`%]")



## Class for parsing and manipulating C++ syntax.
class Syntax:

    ## Regular expression matching comments.
    commentRe  = _commentRe
    ## Syntax.commentRe compiled with regex.compile.
    commentPat = _commentPat
    ## Regular expression matching string literals.
    stringRe   = _stringRe
    ## Syntax.stringRe compiled with regex.compile.
    stringPat  = _stringPat
    ## Regular expression matching string literals.
    charRe     = _charRe
    ## Syntax.charRe compiled with regex.compile.
    charPat    = _charPat
    ## Regular expression matching clipped ranges - comments, string or char literals.
    clipRe     = _clipRe
    ## Syntax.clipRe compiled with regex.compile.
    clipPat    = _clipPat
    ## Regular expression that can be used to find a potential method or function prototype.
    # To confirm if it is the prototype, call Syntax.parseMethPrototype.
    methFinderRe = _methFinderRe


    ## Given a method prototype in the normal form (see Syntax.parseMethPrototype) returns the base name.
    #
    # E.g., passing `"Foo::bar(int i)"` returns `"bar"`.
    def methProtName(prot):
        mres = _methProt1Pat.match(prot)
        assert mres, prot
        return mres.group("name")
    
        
    ## Adds an indentation to all lines.
    #
    # @param indent  String to be inserted.
    def addIndent(code, indent):
        return _lineStartPat.sub(lambda mres: mres.group(0) + indent, code)\


    def _makeNamespacePrefixRe(name):
        return f"namespace{___}(?P<name>{name}){___}{{"


    ## Helper that given a piece of a prototype in the base normal form returns a regular expression that matches it.
    #
    # Base prototype normal form:
    # * no white spaces,
    # * a single `` ` `` in places where a white space is required (e.g., ``unsigned`int``),
    # * sequences `>>` split with `` ` `` if they are not a single operator (e.g. ``vector<vector<int>`>``),
    # * the 3 symbols: `(` `)` `,` followed by `` ` `` (e.g., <int,`pair<int,`int>`>).
    #
    # The backtick `` ` `` should be understand as a separator between tokens or an escape character. The second
    # is utilised in method/function prototypes (see Syntax.makeMethProtRe).
    #
    # @param prot     Piece of a prototype (e.g., type, template arguments) in the base normal form.
    # @param hdSpace  Specifies if the result should match white spaces at the start.
    # @param tlSpace  Specifies if the result should match white spaces at the end.
    # @return         Regular exression matching `prot` in C++ code. Specifically it is `prot` with:
    # * removed `` ` ``,
    # * escaped `regex` symbols,
    # * white space patterns added around symbolic tokens,
    # * it is assumed that only correct C++ code is matched,
    # * currently no support for comments inside prototypes.
    def makeBaseProtRe(prot, hdSpace=False, tlSpace=False):
        re = _cSymbPat.sub(lambda m: f"\\s*{regex.escape(m.group(0), literal_spaces=True)}\\s*", prot)
        if hdSpace: re = r"\s*" + re
        if tlSpace: re = re + r"\s*"
        
        re = regex.sub(r"\b`\b", r"\\s+", re)
        re = (re.replace("`", "")
                .replace(r"\s*\s*", r"\s*"))
        if not hdSpace: re = regex.sub(r"^\\s\*", "", re)
        if not tlSpace: re = regex.sub(r"\\s\*$", "", re)
        return re
    

    ## Given a C++ type in the base normal form returns a regular expression that matches it.
    #
    # This is the same with Syntax.makeBaseProtRe.
    def makeTypeRe(tp):
        return Syntax.makeBaseProtRe(tp)

        #tpRegex = _tpProtSymbPat.sub(lambda m: f"\\s*{m.group()}\\s*", tp)
        #tpRegex = (tpRegex
        #            .replace("`", r",")
        #            .replace(r"\s**\s*", r"\s*\*\s*")
        #            .replace(r"\s*\s*", r"\s*")
        #            .replace(r"\s*%\s*", r"\s+"))
        #tpRegex = regex.sub(r"^\\s\*", "", tpRegex)
        #tpRegex = regex.sub(r"\\s\*$", "", tpRegex)
        #return tpRegex


    ## Given a method or function prototype in the normal form returns a regular expression that matches it.
    #
    # Method/function prototype normal form:
    # * no return type,
    # * prefix before argument parentheses has to be in the base normal form (see Syntax.makeBaseProtRe),
    # * the argument parenteses has to contain only types of arguments in the base normal form split with ``', '`` and
    # no extra spaces,
    # * after the parenteses ``' const'`` is allowed.
    #
    # @param prot  Valid method/function prototype in the normal form (see Syntax.parseMethPrototype).
    # @return      Regular exression matching `prot` in C++ code. Specifically it is `prot` with:
    # * removed `` ` ``,
    # * escaped `regex` symbols,
    # * white space patterns added around symbolic tokens,
    # * patterns for argument names added (matched names are stored in the group `argname`),
    # * patterns for default values added - only literals supported,
    # * it is assumed that only correct C++ code is matched,
    # * currently no support for comments inside prototypes.
    def makeMethProtRe(prot):
        mres = _methProtAPat.fullmatch(prot)
        re = Syntax.makeBaseProtRe(mres.group("hd"))
        if tp := mres.group('targ1'):
            tp2 = Syntax.makeBaseProtRe(tp, True)
            re += (tp2 + 
                   r"\s*\b(?P<argname>\w*)(?:\s*=\s*"f"(?:{_optValRe}))?")
            for tp in mres.captures('targ2'):
                re += (r"\s*,\s*"f"{Syntax.makeBaseProtRe(tp)}"
                       r"\s*\b(?P<argname>\w*)(?:\s*=\s*"f"(?:{_optValRe}))?")
        else:
            re += r"(?P<argname>a^)?" # introduces the required argname group in the expression with a false pattern
        re += r"\s*\)"
        if mods := mres.captures("mod"):
            re += r"\s*" + "\s+".join(mods)
        return re

        #mres = _methProtPat.fullmatch(prot)
        #protRegex = "(?<!::\s*)"
        #if mres.group('cont'):
        #    protRegex += f"{mres.group('cont')}\\s*::\\s*"
        #assert not mres.group('tempArgs'), "Template arguments currenly not supported"
        #protRegex += f"(?P<methname>{mres.group('name')})\\s*\(\\s*"
        #if mres.group('targ1'): #
        #    protRegex += (Syntax.makeBaseProtRe(mres.group('targ1')) + 
        #                  r"\s*(?:\b(?P<argname>\w+)\s*)?(?:=\s*" f"(?:{_optValRe})\\s*)?")
        #    for tp in mres.captures('targ2'):
        #        protRegex += (r",\s*" + Syntax.makeBaseProtRe(tp) + 
        #                      r"\s*(?:\b(?P<argname>\w+)\s*)?(?:=\s*" f"(?:{_optValRe})\\s*)?")
        #else:
        #    protRegex += "(?P<argname>a^)?"
        #protRegex += r"\)"
        #if mres.group('const'):
        #    protRegex += r"\s*const"
        #return protRegex


    ## Returns code without comments.
    def removeComments(code):
        code = regex.sub(r"//.*", "", code)
        code = regex.sub(r"/\*(?:[^\*]|\*[^/])*\*/", "", code)
        return code


    ## Parses template arguments and returns them in the normal form.
    #
    # @param code   The code.
    # @param start  Positions from where to start parsing.
    # @return       Parsed arguments in the normal form or `None`.
    def parseTempArgs(code, start=0):
        mres = _tempArgs0Pat.match(code, start)
        if not mres: return None
        if code[mres.end()] == '>': return ("<>", mres.end() + 1)

        (tp, pos) = Syntax.parseType(code, mres.end())
        args = "<" + tp
        while mres := _tempArgs1Pat.match(code, pos):
            args += ",`"
            (tp, pos) = Syntax.parseType(code, mres.end())
            args += tp
        mres = _tempArgs2Pat.match(code, pos)
        assert mres, f'Expected ">" found "{code[pos:pos+10]}"'
        if args.endswith(">"): args += "`>"
        else:                  args += ">"
        return (args, mres.end())


        # normal form of the type required:
    # - no leading and trailing spaces,
    # - all spaces replaced by single % , no %% allowed,
    # - all , replaced by ` ,
    # - no comments
    def parseType(s, begin=0):
        mres = _tpOps0Pat.match(s, begin)
        tp = mres.group(1)
        pos = mres.end()
        
        if mres := _tpBuiltInPat.match(s, pos):
            tp += mres.group(0)
            pos = mres.end()

        else:
            mres = _tpName0Pat.match(s, pos)
            if not mres: return None

            tp += mres.group(1)
            pos = mres.end()
            match Syntax.parseTempArgs(s, pos):
                case (args, pos): tp += args

            while mres := _tpName1Pat.match(s, pos):
                tp += "::" + mres.group(1)
                pos = mres.end()
                match Syntax.parseTempArgs(s, pos):
                    case (args, pos): tp += args
                    
        if mres := _tpArrPat.match(s, pos):
            tp += mres.group(0)
            pos = mres.end()

        mres = _tpTailPat.match(s, pos)
        tp += mres.group(0)
        pos = mres.end()
        
        mres = _tpOps1Pat.match(s, pos)
        tp += mres.group(0)
        pos = mres.end()

        if mres := _tpFuncPat.match(s, pos):
            return None
            #if ptr := mres.group("ptr"): tp += "{"f"{ptr}""}"
            #(targs, nargs, mods, pos) = Syntax.parseMethDecTail(s, mres.end())
            #tp += "{" + "`".join(targs) + "}" + "%".join(mods)

        tp = _tpSpaceRepPat.sub(lambda m: "`" if m.group(1) else "", tp)
        return (tp, pos)


    def parseExpr(s, begin=0):
        mres = _expr0Pat.match(s, begin)
        if not mres: return None

        expr = mres.group(0)
        begin = mres.end()
        if opSym := mres.group("popen"):
            def readArg(pos):
                match Syntax.parseExpr(s, begin):
                    case (exprArg, pos):
                        mres2 = _expr1Pat.match(s, pos)
                        exprArg += mres2.group(0)
                        pos = mres2.end()
                        return (pos, exprArg)
                    case None:
                        return None
            while res := readArg(begin): 
                begin = res[0]
                expr += res[1]

            mres = _expr2Pat.match(s, begin)
            match opSym, mres.group(0):
                case '(', ')': pass
                case '[', ']': pass
                case _:        return None
            expr += s[begin]
            begin += 1
            
        return (expr, begin)


    def parseMethDecTail(s, begin=0):
        mres = _methDec0aPat.match(s, begin)
        pos = mres.end()
        targs = []
        nargs = []
        def readArg(pos):
            match Syntax.parseType(s, pos):
                case None:
                    return None

                case (tp, pos):
                    mres2 = _methDec1Pat.match(s, pos)
                    name = mres2.group("name")
                    if ptr := mres2.group("ptr"):
                        ptr = _tpSpaceRepPat.sub(lambda m: "`" if m.group(1) else "", ptr)
                    else:
                        ptr = ""
                    pos = mres2.end()
                    if mres2.group("fn"):
                        return None
                        #if ptr: tp += "{"f"{ptr}""}"
                        #match Syntax.parseMethDecTail(s, pos):
                        #    case None: return None
                        #    case (targs2, nargs2, mods2, pos):
                        #        tp += "{"f"{'`'.join(targs2)}""}" + "%".join(mods2)
                    targs.append(tp)
                    nargs.append(name)
                    if (mres2 := _methDec1aPat.match(s, pos)) and (exppos := Syntax.parseExpr(s, mres2.end())):
                        pos = exppos[1]
                    mres2 = _methDec2Pat.match(s, pos)
                    return (mres2.end(), None)
        while (res := readArg(pos)): pos = res[0]

        mres = _methDec3Pat.match(s, pos)
        if not mres: return None
        mods = ["const"] if mres.group(1) else []

        return (targs, nargs, mods, mres.end())

        # no template class support
    # normal form of the prototype required:
    # - no result type at the begining,
    # - normalised types (see above),
    # - no argument names,
    # - exactly 1 space after , and between ) and const at the end, no other spaces,
    # - no comments
    def parseMethPrototype(s, begin=0):
        try:
            mres = _methDec0Pat.match(s, begin)
            if not mres: return None

            contName = mres.group("cont")
            dest = mres.group("dest")

            if op := mres.group("op"):
                id = f"operator{op}"
            elif (pos := mres.end("op")) >= 0:
                match Syntax.parseType(s, pos):
                    case (tp, pos): id = f"operator {tp}"
                    case None: return None
            else:
                pos = mres.end()
                match Syntax.parseTempArgs(s, pos):
                    case (tempArgs, pos): id = mres.group("name") + tempArgs
                    case None:            id = mres.group("name")

            (targs, nargs, mods, pos) = Syntax.parseMethDecTail(s, pos)
        
            prot = contName + "::" if contName else "" 
            prot += "~" if dest else ""
            prot += f"{id}({', '.join(targs)})"
            if mods: prot += " " + " ".join(mods)
            return (prot, nargs, pos)

        except TypeError:
            return None

    def parseClassStructPrefix(kind, name, s, begin=0):
        assert kind in ["class", "struct", "*"]

        if kind == "*": kind = "class|struct"
        re = _classStructHead0Re.format(keyword=kind, name=name)
        mres = regex.match(re, s, pos=begin)
        if not mres: return None
        pos = mres.end()

        match Syntax.parseTempArgs(s, pos):
            case (_, pos): pass

        if mres2 := _classStructHead1Pat.match(s, pos): 
            return (mres.group(1), mres.group(2), mres2.end())
        else:
            return None

    
    # prot in normal form (see above)
    # no template specialization support (e.g. A<std::vector<int>>::foo() )
    def extractProtContainerName(prot):
        mres = _methProt0Pat.match(prot)
        return (mres.group("cont"), prot[mres.end():])
    

    def tempPar(n):
        return "" if n == 0 else r"<(?:[^<>]|{})*>".format(Syntax.tempPar(n-1))


    def nextClipAndLineEnds(code, begin):
        nls = []
        while (mres := _clipBeginPat.search(code, begin)) and mres.group() == "\r\n":
            nls.append(mres.end())
            begin = mres.end()

        if mres:
            match mres.group():
                case "'": 
                    return ((mres.start() + 1, _endCharPat.search(code, mres.end()).start(), 'c'), nls)
                case '"':
                    return ((mres.start() + 1, _endStrPat.search(code, mres.end()).start(), 's'), nls)
                case '//':
                    mres2 = _endComment1Pat.search(code, mres.end())
                    return ((mres.end(), mres2.start(), 'c'), nls + [mres2.end()])
                case '/*':
                    begin = mres.end()
                    while (mres2 := _endCommentNOrNlPat.search(code, begin)) and \
                            mres2.group() == "\r\n":
                        nls.append(mres2.end())
                        begin = mres2.end()
                    return ((mres.end(), mres2.start(), 'C'), nls)
                case _:
                    assert False, mres

        return (None, nls)