# XiTools C++ Crawler

The C++ Crawler is a tool for processing and querying C++ code. It allows advanced searches and replacements.

## Key features

* Searching for regular expressions
* Searching for C++ language constructions (e.g., classes, method declarations, method definitions)
* Omitting comments, string literals or blocks during searches
* Replacing matched code
* Creating scopes in source files (e.g., scoping to specified classes, method bodies)
* Performing searches and replacements restricted to scopes, possibly in many files at once
* Matching scopes (e.g., to filter methods starting with a given prefix)
* Contains a tag system that allows to pass information between scopes and searches (e.g., one can scope to
a class set tagged with names, search for methods and return a result tagged with pairs class + method name)
* Contains features that facilitate loading and managing sources

## Short example

The following example finds all methods containing `health` in their names, in 
all classes and structures with names matching `Cv*Info` across all source files located in the `Sources` directory.

```python
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
```

The prefix `(?i)` in the regular expression stands for *case insensitive*, `(?P<name>...)` for a named capture group, 
`\b` is a 0-width symbol matching a literal edge, `\w` is a literal character and `\s` is a white space. (See
the Python `re` module  documentation for more details.)

The method `tryScopeToClassBody` creates scopes in the underlying object, one per each found class (note that 
structures and unions are also C++ classes). These scopes are tagged with pairs `(kind, name)`, where 
`kind` is: `class`, `struct` or `union` and `name` is the class name.

The `findAll` method searches created scopes. The `scopeTag` switch specifies that each 
returned result should be paired with the tag of the scope where the match was found. The switch `skipBlocks` 
specifies to not search inside blocks.

The pattern `methRe` is an approximation that finds potential method prototypes.
We then verify them by calling `parseMethPrototype`. (This method also verifies the prefixed code to ensure the
validity of the prototype.)

The `intCode` optionally takes 2 arguments: start and end position, and returns the code 
between them - no second argument means *till the end*.

The `start` method of a match object returns its starting position. The `startLoc` method 
returns the pair: line number, in-line character position.


Example output:
```
C:\Projects\Caveman2Cosmos\Sources\CvBonusInfo.h
---
(class) CvBonusInfo::getHealth (28, 6)


C:\Projects\Caveman2Cosmos\Sources\CvBuildingInfo.h
---
(class) CvBuildingInfo::isNoUnhealthyPopulation (58, 7)
(class) CvBuildingInfo::isBuildingOnlyHealthy (59, 7)
...


C:\Projects\Caveman2Cosmos\Sources\CvImprovementInfo.h
---
(class) CvImprovementInfo::getHealthPercent (99, 6)


C:\Projects\Caveman2Cosmos\Sources\CvInfos.h
---
(class) CvSpecialistInfo::getHealthPercent (256, 6)
(class) CvTechInfo::getHealth (378, 6)
(class) CvCivicInfo::getExtraHealth (2937, 6)
...

C:\Projects\Caveman2Cosmos\Sources\CvDummyInfo.cpp
---
(struct) CvDummyInfo::dummyHealth (5, 6)
```

The last entry is added for the presentation reasons.

The example is available in the repository in: *examples/01_search_health_methods*

## Applications

The crawler was used in the [Caveman2Cosmos](https://www.moddb.com/mods/caveman2cosmos) project to:
* conduct simple code qualification of around 17&nbsp;000 methods and add profiling to around 2000 of them,
* comment out all `#if 0` blocks.

The scripts are included as examples.

## Disclaimer

The project is in its infant stage. Backward compatibility is not expected in the first few releases.
Afterward it is going to be highly expected. Releases will be provided with a list of methods that have changed.
Patches (the last number in the version) are going to be backward compatible, as usual.

The current solutions were designed to solve specific problems and need to be refined. For instance,
searching sources was initially based on scopes in source file objects, but searching
without setting scopes appeared handy, thus there are methods like find and findUnscoped, which
probably should be refactored and consolidated. 

<u>The crawler does not currently support Unix-style line endings</u> - but it is of high priority.
If you want to use it for Unix sources, you may convert them to Windows-style, use it, and 
then convert it back.

## Documentation

Documentation available in the repository at: *docs/html/index.html*
