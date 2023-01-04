from tokenize import group
import regex

_commentRe  = r"//.*|/\*(?:[^\*]|\*[^/])*\*/"
_commentPat = regex.compile(_commentRe)
_stringRe   = r'"(?:[^"\\]|\r\n|\\.)*"'
_stringPat  = regex.compile(_stringRe)
_charRe  = r"'(?:[^'\\]|\r\n|\\.)*'"
_charPat = regex.compile(_charRe)
_sxRe    = r"\s|" + _commentRe # c++ space extra pattern (comments are white-spaces)
_sxPat   = regex.compile(_sxRe)
_clipRe  = f"{_commentRe}|{_stringRe}|{_charRe}"
_clipPat = regex.compile(_clipRe)
_optValRe  = f"{_stringRe}|{_charRe}|[\w\.-]+"
_optValPat = regex.compile(_optValRe)

_clipBeginPat   = regex.compile(r"['\"]|//|/\*|\r\n")
_endCharPat     = regex.compile(r"'|\r\n|$")
_endStrPat      = regex.compile(r'"|\r\n|$')
_endComment1Pat = regex.compile(r'\r\n|$')
_endCommentNOrNlPat = regex.compile(r'\*/|\r\n|$')


class Syntax:
    commentRe  = _commentRe
    commentPat = _commentPat
    stringRe   = _stringRe
    stringPat  = _stringPat
    charRe     = _charRe
    charPat    = _charPat


    def makeClassPrefixRe(cname):
        return r"class\s+{}\b(?:[^;\{{]|{})*{{".format(cname, _commentRe)
    

    def makeNamespacePrefixRe(nsname):
        return r"namespace\s+{}\b(?:[^;\{{]|{})*{{".format(nsname, _commentRe)


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
    def makeMethProtRe(prot, *, resultType=False):
        typeRe = r"[^\),]+"
        protRe = r"(?:(\w+)::)?(~?\w+)\(({tp})?(?:, ({tp}))*\)( const)?".format(tp = typeRe)
        mres = regex.fullmatch(protRe, prot)
        if resultType:
            protRegex = r"(?<=(?:^|[;\{{}}])(?:{com}|\s)*)[\w\*&:][\w\*&:<>,\s]*?\s*\b".format(com = _commentRe)
        else:
            protRegex = ""
        if mres.group(1):
            protRegex += f"{mres.group(1)}\\s*::\\s*"
        protRegex += f"(?P<methname>{mres.group(2)})\\s*\(\\s*"
        if mres.group(3): #
            protRegex += Syntax.makeTypeRe(mres.group(3)) + r"\s*(?:\b\w+\s*)?(?:=\s*" f"(?:{_optValRe})\\s*)?"  #
            for tp in mres.captures(4): #
                protRegex += r",\s*" + Syntax.makeTypeRe(tp) + r"\s*(?:\b\w+\s*)?(?:=\s*" f"(?:{_optValRe})\\s*)?"
        protRegex += r"\)"
        if mres.group(5): #
            protRegex += r"\s*const"
        return protRegex


    def removeComments(code):
        code = regex.sub(r"//.*", "", code)
        code = regex.sub(r"/\*(?:[^\*]|\*[^/])*\*/", "", code)
        return code


    # prot in normal form (see above)
    # no template specialization support (e.g. A<std::vector<int>>::foo() )
    def extractProtContainerName(prot):
        div = prot.split("::", 1)
        if len(div) == 1:
            return (None, div[0])
        else:
            return tuple(div)
    

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