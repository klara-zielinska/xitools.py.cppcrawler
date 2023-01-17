from .utils import *
import regex

_commentRe  = r"//.*|/\*(?:[^\*]|\*[^/])*\*/"
_commentPat = regex.compile(_commentRe)
_stringRe   = r'"(?:[^"\\]|\r\n|\\.)*"'
_stringPat  = regex.compile(_stringRe)
_charRe     = r"'(?:[^'\\]|\r\n|\\.)*'"
_charPat    = regex.compile(_charRe)
_sxRe       = r"\s|" + _commentRe # c++ space extra pattern (comments are white-spaces)
_sxPat      = regex.compile(_sxRe)
_clipRe     = f"{_commentRe}|{_stringRe}|{_charRe}"
_clipPat    = regex.compile(_clipRe)
_optValRe   = f"{_stringRe}|{_charRe}|[\w\.-]+"
_optValPat  = regex.compile(_optValRe)

_clipBeginPat   = regex.compile(r"['\"]|//|/\*|\r\n")
_endCharPat     = regex.compile(r"'|\r\n|$")
_endStrPat      = regex.compile(r'"|\r\n|$')
_endComment1Pat = regex.compile(r'\r\n|$')
_endCommentNOrNlPat = regex.compile(r'\*/|\r\n|$')

_methDec0Pat = regex.compile(r"(?:(\w+)\s*::\s*)?(~\s*)?(\w+)\s*\(\s*")
_methDec1Pat = regex.compile(r"\s*(\w+)?(?P<opt>\s*=)?\s*")
_methDec2Pat = regex.compile(r"\s*,?\s*")
_methDec3Pat = regex.compile(r"\)(\s*const)?")
_tpOps0Pat = regex.compile(r"(?!\s)(?:[\*&]|const\b|typename\b|\s+)*")
_tpOps1Pat = regex.compile(r"(?:[\*&]|const\b|\s+)*(?<!\s)")
_tpSpaceRepPat = regex.compile(r"(\b\s+\b)|\s+")
_tpBuiltInPat = regex.compile(r"(?:unsigned\s+)?(?:(?:short|long(?:\s+long)?)(?:\s+int)?|int|char)")
_tpName0Pat = regex.compile(r"\s*(\w+)")
_tpName1Pat = regex.compile(r"\s*::\s*(\w+)")
_tpArrPat = regex.compile(r"\s*\[[^]]*]")
_tpTailPat = regex.compile(r"(?:\s*typename)?")
_tempArgs0Pat = regex.compile(r"\s*<\s*")
_tempArgs1Pat = regex.compile(r"\s*,\s*")
_tempArgs2Pat = regex.compile(r"\s*>")
_lineStartPat = regex.compile(r"^|\r\n")
_indentPat = regex.compile(r"(?<=^|\r\n)([ \t]*+)")
_expr0Pat = regex.compile(r"\s*+[^\(\)\[\],]+(?P<popen>\(|\[)?(?<!\s)")
_expr1Pat = regex.compile(r"\s*,?\s*")
_expr2Pat = regex.compile(r"[\)\]]")
_classStructHead0Re = r"\b{keyword}\s+{name}\b\s*"
_classStructHead1Re = r"\s*(?::(?!:)(?:[^;\{]|"f"{_commentRe}"r")*+)?(?=\{)"


class Syntax:
    commentRe  = _commentRe
    commentPat = _commentPat
    stringRe   = _stringRe
    stringPat  = _stringPat
    charRe     = _charRe
    charPat    = _charPat

    
    def unindent(code):
        comPrefix = maxCommonPrefix(_indentPat.findall(code))
        return regex.sub(f"(^|\r\n){comPrefix}", lambda mres: mres.group(1), code)
        

    def indent(code, ind):
        return _lineStartPat.sub(lambda mres: mres.group(0) + ind, code)


    #def makeClassPrefixRe(cname):
    #    return _classStructPrefixRe.format(keyword="class", name=cname)


    #def makeStructPrefixRe(sname):
    #    return _classStructPrefixRe.format(keyword="struct", name=sname)
    

    def makeNamespacePrefixRe(nsname):
        return r"namespace\s+{}\b(?:\s|{})*{{".format(nsname, _commentRe)


    def makeDirectCallRe(methnames):
        return  r"([^\w\.:]|this->|[^-]>)(" + r"\(|".join(methnames) + r"\()"


    # normal form of the type required:
    # - no leading and trailing spaces,
    # - all spaces replaced by single % , no %% allowed,
    # - all , replaced by ` ,
    # - no comments
    def makeTypeRe(tp):
        tpRegex = regex.sub(r"[<>\*&`%]|::", lambda m: f"\\s*{m.group()}\\s*", tp)
        tpRegex = (tpRegex
                    .replace("`", r",")
                    .replace(r"\s**\s*", r"\s*\*\s*")
                    .replace(r"\s*\s*", r"\s*")
                    .replace(r"\s*%\s*", r"\s+"))
        tpRegex = regex.sub(r"^\\s\*", "", tpRegex)
        tpRegex = regex.sub(r"\\s\*$", "", tpRegex)
        return tpRegex


    # no template class support
    # normal form of the prototype required:
    # - no result type at the begining,
    # - normalised types (see above),
    # - no argument names,
    # - exactly 1 space after , and between ) and const at the end, no other spaces,
    # - no comments
    def makeMethProtRe(prot):
        typeRe = r"[^\),]+"
        protRe = r"(?:(\w+)::)?(~?\w+)\(({tp})?(?:, ({tp}))*\)( const)?".format(tp = typeRe)
        mres = regex.fullmatch(protRe, prot)
        if False: # to do
            protRegex = r"(?<=(?:^|[;\{{}}])(?:{com}|\s)*)[\w\*&:][\w\*&:<>,\s]*?\s*\b".format(com = _commentRe)
        else:
            protRegex = "(?<!::\s*)"
        if mres.group(1):
            protRegex += f"{mres.group(1)}\\s*::\\s*"
        protRegex += f"(?P<methname>{mres.group(2)})\\s*\(\\s*"
        if mres.group(3): #
            protRegex += (Syntax.makeTypeRe(mres.group(3)) + 
                          r"\s*(?:\b(?P<argname>\w+)\s*)?(?:=\s*" f"(?:{_optValRe})\\s*)?")
            for tp in mres.captures(4):
                protRegex += (r",\s*" + Syntax.makeTypeRe(tp) + 
                              r"\s*(?:\b(?P<argname>\w+)\s*)?(?:=\s*" f"(?:{_optValRe})\\s*)?")
        else:
            protRegex += "(?P<argname>a^)?"
        protRegex += r"\)"
        if mres.group(5):
            protRegex += r"\s*const"
        return protRegex


    def removeComments(code):
        code = regex.sub(r"//.*", "", code)
        code = regex.sub(r"/\*(?:[^\*]|\*[^/])*\*/", "", code)
        return code


    def parseTempArgs(s, begin=0):
        mres = _tempArgs0Pat.match(s, begin)
        if not mres: return None
        if s[mres.end()] == '>': return ("<>", mres.end() + 1)

        (tp, pos) = Syntax.parseType(s, mres.end())
        args = "<" + tp
        while mres := _tempArgs1Pat.match(s, pos):
            args += "`"
            (tp, pos) = Syntax.parseType(s, mres.end())
            args += tp
        mres = _tempArgs2Pat.match(s, pos)
        assert mres, f'Expected ">" found "{s[pos:pos+10]}"'
        return (args + ">", mres.end())


    def parseType(s, begin=0):
        mres = _tpOps0Pat.match(s, begin)
        tp = mres.group(0)
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

        tp = _tpSpaceRepPat.sub(lambda m: "%" if m.group(1) else "", tp)
        return (tp, mres.end())


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


    def parseMethDeclaration(s, begin=0):
        mres = _methDec0Pat.match(s, begin)
        if not mres: return None

        contName = mres.group(1)
        destru = mres.group(2)
        name = mres.group(3)
        begin = mres.end()

        targs = []
        nargs = []
        if s[mres.end()] != ')':
            def readArg(pos):
                match Syntax.parseType(s, pos):
                    case (tp, pos):
                        targs.append(tp)
                        mres2 = _methDec1Pat.match(s, pos)
                        nargs.append(mres2.group(1))
                        pos = mres2.end()
                        if mres2.group("opt") and (res := Syntax.parseExpr(s, pos)):
                            pos = res[1]
                        mres2 = _methDec2Pat.match(s, pos)
                        return (mres2.end(), None)
                    case None:
                        return None
            while (res := readArg(begin)): begin = res[0]

        mres = _methDec3Pat.match(s, begin)
        if not mres: return None
        const = mres.group(1) is not None
        
        prot = contName + "::" if contName else "" 
        prot += "~" if destru else ""
        prot += name + "(" + ", ".join(targs) + ")"
        if const: prot += " const"
        return (prot, nargs, mres.end())


    def parseClassStructPrefix(kind, name, s, begin=0):
        assert kind in ["class", "struct", None]

        if not kind: kind = "class|struct"
        re = _classStructHead0Re.format(keyword=kind, name=name)
        mres = regex.match(re, s, pos=begin)
        if not mres: return None
        pos = mres.end()

        match Syntax.parseTempArgs(s, pos):
            case (_, pos): pass

        mres = regex.match(_classStructHead1Re, s, pos=pos)
        if mres: return (s[begin:mres.end()], mres.end())
        else:    return None

    
    # prot in normal form (see above)
    # no template specialization support (e.g. A<std::vector<int>>::foo() )
    def extractProtContainerName(prot):
        mres = _methDec0Pat.match(prot)
        return (mres.group(1), prot[mres.start(3):])
    

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