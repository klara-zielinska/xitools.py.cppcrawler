from xitools.cppcrawler import *
crawler = CppCrawler("Sources")

methSearchRe = r"(?i)\b(?P<name>\w*health\w*)\s*\("
for src in crawler.loadSourceFiles(["*.h", "*.cpp"]):
    if src.tryScopeToClassBody("class|struct", r"Cv\w*Info"):
        found = []
        for (rmatch, stag) in src.findAll(methSearchRe, scopeTag=True, skipBlocks=True):
            if Syntax.parseMethPrototype(src.intCode(rmatch.start())):
                found.append((rmatch, stag))

        if found:
            print("\n\n" + src.filepath() + "\n---")
            for rmatch, (kind, name) in found:
                print(f'({kind}) {name}::{rmatch.group("name")}', rmatch.startLoc())
                
