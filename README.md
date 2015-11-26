# feaders
/ˈfed.ərs/

Fedora headers searcher is a tool that analyzes `#include` directives in C/C++ header/source files and tries to map them to a Fedora RPM package that provides such file. Feaders uses `DNF` and it's `repoquery` plugin to search entire repository for provided files. The current approach for the search is rather brute-force, that being said, there's a lot of space for improvement and the performance so far has not been great.

### Usage

```bash
$ ./feaders file.c file2.h
```

Or more conveniently:

```bash
$ ./feaders -r /path/to/project
```

Which allows to eliminate includes relative to the root and also automatically searches for source/header files.
Good choice of root will allow the system to eliminate more candidates, directories containing `configure.ac` or `CMakeList.txt` are good starting fit for this parameter, but this indeed depends on project structure and include path configuration.

### Example
What headers are needed for compilation of `bcrypt` native extension for Ruby?

```bash
$ ./feaders -r bcrypt-ruby/ext/mri/
ruby-devel-0:2.2.3-44.fc22.x86_64
```
