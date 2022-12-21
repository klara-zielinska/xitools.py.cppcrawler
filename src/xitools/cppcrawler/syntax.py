from tokenize import group
import regex

_commentRe  = r"//.*|/\*(?:[^\*]|\*[^/])*\*/"
_commentPat = regex.compile(_commentRe)
_stringRe   = r'"(?:[^"\\]|\r\n|\\.)*"'
_stringPat  = regex.compile(_stringRe)
_charRe  = r"'(?:[^'\\]|\r\n|\\.)*'"
_charPat = regex.compile(_charRe)
_sxRe    = r"\s|" + _commentRe # c++ space-extra pattern (comments are white-spaces)
_sxPat   = regex.compile(_sxRe)
_clipRe  = f"{_commentRe}|{_stringRe}|{_charRe}"
_clipPat = regex.compile(_clipRe)
_optValRe  = f"{_stringRe}|{_charRe}|[\w-\.]+"
_optValPat = regex.compile(_optValRe)

_clipBeginPat   = regex.compile(r"['\"]|//|/\*|\r\n")
_endCharPat     = regex.compile(r"'|\r\n|$")
_endStrPat      = regex.compile(r'"|\r\n|$')
_endComment1Pat = regex.compile(r'\r\n|$')
_endCommentNOrNlPat = regex.compile(r'\*/|\r\n|$')


class Syntax:

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
    def makeMethProtRe(prot):
        typePat = r"[^\),]+"
        #protPat = r"(\w+)::(\w+)\(({tp})?(?:, ({tp}))*\)( const)?".format(
        protPat = r"(~?\w+)\(({tp})?(?:, ({tp}))*\)( const)?".format(
            tp = typePat)
        mres = regex.fullmatch(protPat, prot)
        #protRegex = r"{}\s*::\s*{}\s*\(\s*".format(mres.group(1), mres.group(2))
        protRegex = r"{}\s*\(\s*".format(mres.group(1))
        if mres.group(2): #
            protRegex += Syntax.makeTypeRe(mres.group(2)) + r"\s*(?:\b\w+\s*)?(?:=\s*" f"(?:{_optValRe})\\s*)?"  #
            for tp in mres.captures(3): #
                protRegex += r",\s*" + Syntax.makeTypeRe(tp) + r"\s*(?:\b\w+\s*)?(?:=\s*" f"(?:{_optValRe})\\s*)?"
        protRegex += r"\)"
        if mres.group(4): #
            protRegex += r"\s*const"
        return protRegex


    def removeComments(code):
        code = regex.sub(r"//.*", "", code)
        code = regex.sub(r"/\*(?:[^\*]|\*[^/])*\*/", "", code)
        return code


    #_prefMethProt = regex.compile(r"(\w+)::(.)")
    # prot in normal form (see above)
    def extractMethProtClass(prot):
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