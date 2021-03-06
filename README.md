# feaders
/ˈfed.ərs/

Fedora headers searcher is a tool that analyzes `#include` directives in C/C++ header/source files and tries to map them to a Fedora RPM package that provides such file. Feaders uses `DNF` and it's `repoquery` plugin to search entire repository for provided files. The current approach for the search is rather brute-force, that being said, there's a lot of space for improvement and the performance so far has not been great.

### Installation

You can grab a package for your Fedora (22/23/Rawhide) from my COPR:

```
https://copr.fedoraproject.org/coprs/podvody/Feaders/
```

If you want to quickly test how/if it works, you can simply clone the repo and start working with the `feaders` executable directly.

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

To use `feaders-server` for file resolution use this form:
```bash
$ ./feaders -f server_url -r /path/to/project
```

### Feaders-Server
Description and rationale for this component can be found [in a separate document](http://github.com/shaded-enmity/feaders/tree/master/server). Long story short, it makes the lookup/search lighting fast.

### Installation

List of needed packages:
```
python-requests
librepo
```

### Example
What headers are needed for compilation of `bcrypt` native extension for Ruby?

```bash
$ ./feaders -r bcrypt-ruby/ext/mri/
ruby-devel-0:2.2.3-44.fc22.x86_64
```

Example verbose run against `Pillow`'s native extension (Python):
```bash
$ ./feaders -v -r ../Pillow/
-> probing root '../Pillow/'
=> include 'py3.h' found in '../Pillow/' or is a libc include
=> include 'unistd.h' found in '../Pillow/' or is a libc include
=> include 'string.h' found in '../Pillow/' or is a libc include
=> include 'math.h' found in '../Pillow/' or is a libc include
=> include 'stdlib.h' found in '../Pillow/' or is a libc include
=> include 'stdio.h' found in '../Pillow/' or is a libc include
=> include 'memory.h' found in '../Pillow/' or is a libc include
=> include 'setjmp.h' found in '../Pillow/' or is a libc include
=> include 'time.h' found in '../Pillow/' or is a libc include
=> include 'pthread.h' found in '../Pillow/' or is a libc include
=> include 'ctype.h' found in '../Pillow/' or is a libc include
=> include 'stdint.h' found in '../Pillow/' or is a libc include
-> elimination statistics:
==> original files: 106
==> eliminated includes: 12
==> searched includes: 31
==> duplicate includes: 63
==> ratio: 2.41935483871
libjpeg-turbo-devel-0:1.4.0-2.fc22.x86_64
libtiff-devel-0:4.0.3-20.fc22.x86_64
zlib-devel-0:1.2.8-7.fc22.x86_64
python-devel-0:2.7.10-8.fc22.x86_64
tk-devel-1:8.6.4-2.fc22.x86_64
openjpeg-devel-0:1.5.1-14.fc22.x86_64
libwebp-devel-0:0.4.4-1.fc22.x86_64
python3-devel-0:3.4.2-6.fc22.x86_64
lcms2-devel-0:2.7-1.fc22.x86_64
```

Using the `feaders-server` to lookup Ruby's `nokogiri` package:
```bash
$ ./feaders -f http://localhost:5000 -r ../nokogiri/
libxslt-devel-0:1.1.28-11.fc23.x86_64
memchan-devel-0:2.3-9.fc23.x86_64
ruby-devel-0:2.2.3-44.fc24.x86_64
```
