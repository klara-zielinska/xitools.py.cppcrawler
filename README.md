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

## Documentation

Documentation available in the repository: *docs/html/index.html*