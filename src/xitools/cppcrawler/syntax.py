from .utils import *
import regex


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

_opSym0Re = f"(?:(?P<brackR>\\({___}\\))|(?P<brackS>\\[{___}])"r"|[-+*/%^&|~!=<>,]{1,3})"
_ptrArgOps0Re = r"(?:\s*[&*]\s*|\s*const\b\s*)+"


# Warning: can find an expression or an initializer
_methFinderRe = (f"(?:{_idRe}{___}::{___})?"
                 r"(?:~|\boperator\b"f"|{_idRe}(?:{___}<(?:{_clipRe}|[^;{{}}])*+>)?){___}"r"\(")


# no function types support
_methProtAPat = regex.compile(r"(?P<hd>(?:[^(]|\(`)++\()"
                              r"(?:(?P<targ1>{tp})(?:, (?P<targ2>{tp}))*+)?"
                              r"\)(?: (?P<mod>\w++))*".format(tp = r"(?:[^),]|[),]`)++"))
_methProtPat = regex.compile(r"(?:(?P<cont>\w+)::)?(?P<name>operator\(\)|~?[^(]+)(?P<tempArgs><[^(]*>)?"
                             r"\((?P<targ1>{tp})?(?:, (?P<targ2>{tp}))*\)(?P<const> const)?".format(tp = "[^),]+"))
_methProt0Pat = regex.compile(r"(?:(?P<cont>\w+)::)?")
_methProt1Pat = regex.compile(r"\([^`]")
_methProt2Pat = regex.compile(r"(?:(?P<seg>)::)?(?P<seg>[^:]+)(?:::(?P<seg>[^:]+))*")
_methDec0Pat = regex.compile(r"(?<!(?:,)\s*)(?:\b(?P<cont>\w+)\s*::\s*)?(?P<dest>~\s*)?"
                             r"\b(?:operator\b\s*(?P<op>"f"(?:{_opSym0Re})?)"
                             r"|(?P<name>\w+)\s*(?=(?P<x>\(|<)))")
_methDec00Pat = regex.compile(f"(?<!(?:,){___})")
_methDec01Pat = regex.compile(f"(?P<nssep>::{___})?"
                              f"(?:\\boperator\\b{___}(?P<op>{_opSym0Re})?{___}|"
                              f"(?P<dest>~{___})?\\b(?P<id>\\w+){___})")
_methDec0aPat = regex.compile(f"\\({___}")
_methDec1Pat = regex.compile(f"{___}"r"(?P<name>\w*)"f"{___}")
_methDec1aPat = regex.compile(f"{___}(?P<opt>=){___}")
_methDec2Pat = regex.compile(f"{___},?{___}")
_methDec3Pat = regex.compile(f"{___}const")
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
_expr2Pat = regex.compile(r"[)\]]")
_classHead0Pat = regex.compile(f"\\b(?P<kind>class|struct|union){___}(?P<name>\\w+){___}")
_classHead1Pat = regex.compile(f"(?P<mod>final)?{___}"r"(?::(?!:)(?:"f"{__}"r"|[^;{])*+)?(?=;|\{)")
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
    # * sequences `>>` split with `` ` `` if they are not a single operator (e.g., ``vector<vector<int>`>``),
    # * the 3 symbols: `(` `)` `,` followed by `` ` `` (e.g., <int,`pair<int,`int>`>).
    #
    # The backtick `` ` `` should be understand as a separator between tokens or an escape character. 
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
    # * argument parenteses has to contain only types of arguments in the base normal form split with ``", "`` and
    # no extra spaces,,
    # * argument parentheses are not escaped with `` ` ``
    # * after the parenteses ``" const"`` is allowed.
    #
    # E.g., ``Foo::bar(unsigned`int, vector<pair<int,`int>`>*) const`` .
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


    ## Given a method or function prototype in the normal form returns its id-expression in list form.
    #
    # @param prot  Method or function prototype in the normal form (see Syntax.makeMethProtRe).
    # @return      Pair `(id, rem)`, where `id` is a qualified id in the form of a list of name specifiers 
    #              (the specifiers of `A::B` are `A`, `B`) and `rem` is the reimaing prototype part.
    #
    # @par  Example
    # ``extractMethProtId("::std::vector<std::pair<int,`int>`>::clear()")``  
    # returns ``(["", "std", "vector<std::pair<int,`int>`>", "clear"], "()")``
    def extractMethProtId(prot):
        argsStart = _methProt1Pat.search(prot).start()
        idExpr = prot[:argsStart]
        id = []
        buf = ""
        tempArgsOpen = 0
        for seg in _methProt2Pat.fullmatch(idExpr).captures("seg"):
            tempArgsOpen += seg.count("<") - seg.count(">")
            if tempArgsOpen == 0:
                id.append(buf + seg)
                buf = ""
            else:
                buf += seg + "::"
        assert tempArgsOpen == 0, f"Prototype illformed: {prot}"
        return (id, prot[argsStart:])


    ## Given a method or function prototype in the normal form returns its id-expression in list form.
    #
    # @param prot  Method or function prototype in the normal form (see Syntax.makeMethProtRe).
    # @return      Pair `(baseProt, idPref)`, where `baseProt` is the suffix of `prot` starting from the method's name 
    #              and `idPref` is the remaining prefix split into a list of id specifiers.
    #
    # @par  Example
    # ``extractMethBaseProt("::std::vector<std::pair<int,`int>`>::clear()")``  
    # returns ``("clear()", ["", "std", "vector<std::pair<int,`int>`>"])``
    def extractMethBaseProt(prot):
        (id, rem) = Syntax.extractMethProtId(prot)
        return (id[-1] + rem, id[:-1])


    ## Returns code without comments.
    def removeComments(code):
        code = regex.sub(r"//.*", "", code)
        code = regex.sub(r"/\*(?:[^\*]|\*[^/])*\*/", "", code)
        return code

    
    ## Parses a type and returns it in the base prototype normal form.
    #
    # @param code   The code.
    # @param start  Starting position.
    # @return       Pair `(tp, end)` or `None`, where `tp` is the parsed type in the base prtotype normal 
    #               form (see Syntax.makeBaseProtRe) and `end` is the end position of the parsed code piece.
    #
    # @remark  Currently no support for function types, possibly more (the autor hasn't checked
    #          the whole C++ syntax).
    #
    # @par  Example
    # Input: `"std::vector <std::pair<unsigned int , const char *>>"`   
    # Output: ``"std::vector<std::pair<unsigned`int,`const`char*>`>"``
    def parseType(code, start=0):
        mres = _tpOps0Pat.match(code, start)
        tp = mres.group(1)
        pos = mres.end()
        
        if mres := _tpBuiltInPat.match(code, pos):
            tp += mres.group(0)
            pos = mres.end()

        else:
            mres = _tpName0Pat.match(code, pos)
            if not mres: return None

            tp += mres.group(1)
            pos = mres.end()
            match Syntax._parseTempArgsApp(code, pos):
                case (args, pos): tp += args

            while mres := _tpName1Pat.match(code, pos):
                tp += "::" + mres.group(1)
                pos = mres.end()
                match Syntax._parseTempArgsApp(code, pos):
                    case (args, pos): tp += args
                    
        if mres := _tpArrPat.match(code, pos):
            tp += mres.group(0)
            pos = mres.end()

        mres = _tpTailPat.match(code, pos)
        tp += mres.group(0)
        pos = mres.end()
        
        mres = _tpOps1Pat.match(code, pos)
        tp += mres.group(0)
        pos = mres.end()

        tp = _tpSpaceRepPat.sub(lambda m: "`" if m.group(1) else "", tp)
        return (tp, pos)
    

    def _parseTempArgsApp(code, start=0):
        mres = _tempArgs0Pat.match(code, start)
        if not mres: return None
        if code[mres.end()] == '>': return ("<>", mres.end() + 1)

        match Syntax.parseType(code, mres.end()):
            case None:      return None
            case (tp, pos): pass;
        args = "<" + tp
        while mres := _tempArgs1Pat.match(code, pos):
            args += ",`"
            (tp, pos) = Syntax.parseType(code, mres.end())
            args += tp

        mres = _tempArgs2Pat.match(code, pos)
        if not mres: return None

        if args.endswith(">"): args += "`>"
        else:                  args += ">"
        return (args, mres.end())


    def _parseMethDefaultExpr(code, start=0):
        mres = _expr0Pat.match(code, start)
        if not mres: return None

        expr = mres.group(0)
        start = mres.end()
        if opSym := mres.group("popen"):
            def readArg(pos):
                match Syntax._parseMethDefaultExpr(code, start):
                    case (exprArg, pos):
                        mres2 = _expr1Pat.match(code, pos)
                        exprArg += mres2.group(0)
                        pos = mres2.end()
                        return (pos, exprArg)
                    case None:
                        return None
            while res := readArg(start): 
                start = res[0]
                expr += res[1]

            mres = _expr2Pat.match(code, start)
            match opSym, mres.group(0):
                case '(', ')': pass
                case '[', ']': pass
                case _:        return None
            expr += code[start]
            start += 1
            
        return (expr, start)


    def _parseMethArgs(code, start=0):
        mres = _methDec0aPat.match(code, start)
        if not mres: return None

        pos = mres.end()
        targs = []
        nargs = []
        def readArg(pos):
            match Syntax.parseType(code, pos):
                case None:
                    return None

                case (tp, pos):
                    mres2 = _methDec1Pat.match(code, pos)
                    if not mres2: return None

                    name = mres2.group("name") or None # if name = "", then None
                    pos = mres2.end()
                    targs.append(tp)
                    nargs.append(name)
                    if (    mres3 := _methDec1aPat.match(code, pos)) and (
                            exppos := Syntax._parseMethDefaultExpr(code, mres3.end())):
                        pos = exppos[1]
                    mres4 = _methDec2Pat.match(code, pos)
                    return (mres4.end(), None)
        while (res := readArg(pos)): pos = res[0]
        
        if code[pos] == ")":
            return (targs, nargs, pos + 1)
        else:
            return None

    
    ## Parses a method prototype and returns it in the normal form.
    #
    # @param code   The code.
    # @param start  Starting position.
    # @return       Pair `(prot, end)` or `None`, where `prot` is the parsed prototype in the normal 
    #               form (see Syntax.makeMethProtRe) and `end` is the end position of the parsed code piece.
    #
    # @remark  Currently no support for function types, volatail modifiers, possibly more (the autor hasn't checked
    #          the whole C++ syntax).
    #
    # @par  Example
    # Input: `"std::vector <std::pair<unsigned int , const char *>>"`   
    # Output: ``"std::vector<std::pair<unsigned`int,`const`char*>`>"``
    def parseMethPrototype(code, start=0):
        mres = _methDec00Pat.match(code, start)
        if not mres: return None

        prot = ""
        pos = start
        
        while mres := _methDec01Pat.match(code, pos):
            if mres.group("nssep"): prot += "::"
            
            pos = mres.end()
            if mres.group("id"):
                if mres.group("dest"):
                    prot += "~" + mres.group("id")
                    break
                else:
                    prot += mres.group("id")
                    match Syntax._parseTempArgsApp(code, pos):
                        case (tempArgs, pos): prot += tempArgs

            else: # operator
                if op := mres.group("op"):
                    if mres.group("brackR"):
                        prot += f"operator()"
                    elif mres.group("brackS"):
                        prot += f"operator[]"
                    else:
                        prot += f"operator{op}"
                else:
                    match Syntax.parseType(code, pos):
                        case (tp, pos): prot += f"operator`{tp}"
                        case None:      return None
                break

        if not prot: return None

        match Syntax._parseMethArgs(code, pos):
            case (targs, nargs, pos): prot += f"({', '.join(targs)})"
            case None:                return None
            
        if mres := _methDec3Pat.match(code, pos):
            prot += " const"
            pos = mres.end()

        return (prot, nargs, pos)


    ## Parses a class, structure or union prefix.
    #
    # Parsing ends on `;` or `{`.
    #
    # @param code   The code.
    # @param start  Starting position.
    # @return       Tuple `(kind, name, mods, tempArgs, end)` or `None`, where:
    # * `kind` is: `"class"`, `"struct"` or `"union"`,
    # * `tempArgs` are template arguments in the base normal form (see Syntax.makeBaseProtRe) or `None`,
    # * `mods` is a set of modifiers: either `{ "final" }` or empty.
    # * `end` is the end position of the parsed code piece (`code[end]` is `;` or `{`).
    def parseClassPrefix(code, start=0):
        mres = _classHead0Pat.match(code, start)
        if not mres: return None

        kind = mres.group("kind")
        name = mres.group("name")
        pos  = mres.end()

        match Syntax._parseTempArgsApp(code, pos):
            case None:            tempArgs = None
            case (tempArgs, pos): pass

        if mres := _classHead1Pat.match(code, pos):
            return (kind, name, tempArgs, set(mres.captures("mod")), mres.end())
        else:
            return None
