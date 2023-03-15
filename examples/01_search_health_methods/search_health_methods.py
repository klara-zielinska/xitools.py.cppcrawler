from xitools.cppcrawler import *
crawler = CppCrawler("Sources")

methSearchRe = r"(?i)\b(?P<name>\w*health\w*)\s*\("
for src in crawler.loadSourceFiles(["*.h", "*.cpp"]):
    if src.tryScopeToClassBody("class|struct", r"Cv\w*Info"):
        found = []
        for (mch, tag) in src.findAll(methSearchRe, scopeTag=True, skipBlocks=True):
            if Syntax.parseMethPrototype(src.intCode(), mch.intStart()):
                found.append((mch, tag))

        if found:
            print("\n\n" + src.filepath() + "\n---")
            for mch, (kind, name) in found:
                print(f'({kind}) {name}::{mch.group("name")}', mch.startLoc())
                
