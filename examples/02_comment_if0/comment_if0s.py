from xitools.cppcrawler import *
crawler = CppCrawler("Sources", backupDir="Backup", encoding="utf-8")

def srcMatchMsg(src, match, msg): 
    return f"{src.filepath()}:{match.startLoc()[0]}: {msg}"

# given an #if... directive position, finds the corresponding #else, #elif or #endif (whichever comes first)
def findEndifElse(src, pos, *, findElse=True):
    elseRe = r"|else|elif" if findElse else ""
    preprocRe = r"(?<=^|\n)[ \t]*#(?P<dir>if|endif"f"{elseRe}).*\n?" # matches #ifdef, #ifndef
    while match := src.findUnscoped(preprocRe, pos):
        if match.group("dir") == "if":
            match2 = findEndif(src, match.end())
            assert match2, srcMatchMsg(src, match, "#if has no #endif")
            pos = match2.end()
        else:
            return match
    return None

def findEndif(src, pos):
    return findEndifElse(src, pos, findElse=False)

toSave = set()

for src in crawler.loadSourceFiles(["*.h", "*.cpp"]):
    pos = 0
    while match := src.findUnscoped(r"(?<=^|\n)[ \t]*#if[ \t]+0\b.*\n?", pos):
        match2 = findEndifElse(src, match.end())
        assert match2, srcMatchMsg(src, match, "#if has no #endif")
        pos = match2.end()

        match match2.group("dir"):
            case "elif":
                print(srcMatchMsg(src, match2, "#elif not supported"))
                continue

            case "else":
                match3 = findEndif(src, match2.end())
                assert match3, srcMatchMsg(src, match, "#if has no #endif")
                src.insert(match3.start(), "//") # code modifications invalidate matched positions behind, thus
                                                 # we need to perform them latter first

        src.setScope(match.start(), match2.start())
        src.replace(r"(?<=^|\n)", "//")
        toSave.add(src)
        # after inserting // pos can be inside a comment - this is ok, because findUnscoped omits comments

crawler.saveSources(toSave)

print("SCRIPT FINISHED")
