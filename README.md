# feaders
/ˈfed.ərs/

Fedora headers searcher is a tool that analyzes `#include` directives in C/C++ header/source files and tries to map them to a Fedora RPM package that provides such file, all in 42 lines. Feaders uses `DNF` and it's `repoquery` plugin to search entire repository for provided files. The current approach for the search is rather brute-force, that being said, there's a lot of space for improvement and the performance so far has not been great.

### Usage

```bash
$ ./feaders file.c file2.h
```

Or more conveniently:

```bash
$ ./feaders $(find /path/to/project -name '*.[hc]')
```

### Example
What headers are needed for compilation of `bcrypt` native extension for Ruby?

```bash
$ ./feaders $(find bcrypt-ruby/ext/mri/ -name '*.[hc]')
ruby-devel-0:2.2.3-44.fc22.x86_64
glibc-headers-0:2.21-8.fc22.x86_64
```
