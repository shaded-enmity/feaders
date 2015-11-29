#!/usr/bin/python -tt
# vim: set fileencoding=utf-8
# /ˈfed.ərs/ Pavel Odvody <podvody@redhat.com> 2015 - MIT License
from flask import Flask, redirect, request, render_template, url_for
import glob
import json
import librepo
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

app = Flask(__name__)

def callback(data, total_to_download, downloaded):
  PROGRESSBAR_LEN = 50
  if total_to_download <= 0:
    return
  completed = int(downloaded / (total_to_download / PROGRESSBAR_LEN))
  print "[%s%s] %8s/%8s (%s)\r" % ('#'*completed, 
                                   '-'*(PROGRESSBAR_LEN-completed), 
                                   int(downloaded), 
                                   int(total_to_download), 
                                   data),
  sys.stdout.flush()

def get_args():
  arch = request.args.get('arch', Repositories.DEFAULT_ARCH)
  name = request.args.get('name', Repositories.DEFAULT_NAME)
  release =  request.args.get('release', Repositories.DEFAULT_RELEASE)
  return arch, name, release

class RepoType(object):
  (Invalid, Fedora, Centos) = [0, 1, 2]

  @staticmethod
  def from_string(s):
    return {'fedora': RepoType.Fedora, 'centos': RepoType.Centos}.get(s.lower())

class Repositories(object):
  FEDORA_METALINK_URL = "https://mirrors.fedoraproject.org/metalink?repo={}-{}&arch={}"
  CENTOS_METALINK_URL = "http://mirrorlist.centos.org/?release={}&arch={}&repo={}"
  CENTOS_REPOS = ('os', 'updates')
  DEFAULT_ARCH = 'x86_64'
  DEFAULT_NAME = 'fedora'
  DEFAULT_RELEASE = 'rawhide'

class RepoHandler(object):
  def __init__(self, base_path):
    self._base_path = base_path

  @property
  def base_path(self):
    return self._base_path

  def _ensure_paths(self, name, ver, arch):
    # make sure we can write to './#{name}/#{ver}/#{arch}/'
    named = os.path.join(self.base_path, name)
    versioned = os.path.join(named, ver)
    arched = os.path.join(versioned, arch)
    if os.path.isdir(named):
      if not os.path.isdir(versioned):
        os.mkdir(versioned)
        os.mkdir(arched)
      else:
        if not os.path.isdir(arched):
          os.mkdir(arched)
    else:
      os.mkdir(named)
      os.mkdir(versioned)
      os.mkdir(arched)
    return arched

  def _handle_suffix(self, db, path, suffix, extract_cmd, save_as):
    name = db[:-len(suffix)]
    # get the filename
    _, fname = os.path.split(name)
    subprocess.check_call(extract_cmd)
    target = os.path.join(path, save_as)
    # if the item was already cached, remove it
    if os.path.exists(target):
      os.remove(target)
    shutil.copyfile(name, target)
    os.remove(name)
    return target

  def _cache_db(self, db, path, save_as):
    if db.endswith('.xz'):
      return self._handle_suffix(db, path, '.xz', ["xz", "-d", db], save_as)
    elif db.endswith('.bz2'):
      return self._handle_suffix(db, path, '.bz2', ["bzip", "-d", db], save_as)
    else:
      raise ValueError("_cache_db: unknown suffix: {}".format(db))

  def _librepo_prepare(self, path):
    # prepare Handle, Result and create temp dir for downloaded data
    h = librepo.Handle()
    r = librepo.Result()
    h.repotype = librepo.LR_YUMREPO
    h.destdir = tempfile.mkdtemp()
    h.fastestmirror = True
    h.progresscb = callback
    h.progressdata = path
    return h, r, h.destdir

  def _cache_fedora(self, name, ver, arch):
    # create cache directory
    path = self._ensure_paths(name, ver, arch)
    # prepare request
    h, r, tmp = self._librepo_prepare(path)
    # point the request at Fedora repos
    h.mirrorlist = Repositories.FEDORA_METALINK_URL.format(name, ver, arch)

    try:
      h.perform(r)
    except librepo.LibrepoException as e:
      rc, msg, general_msg  = e
      print "Error: %s" % msg

    # read back the results
    data = r.getinfo(librepo.LRR_YUM_REPO)

    self._cache_db(data['filelists_db'], path, 'files.sqlite')
    self._cache_db(data['primary_db'], path, 'primary.sqlite')

    # return all cached files
    return filter(None, [x.strip() for x in os.listdir(path)])

  def _cache_centos(self, name, ver, arch):
    # create cache directory
    path = self._ensure_paths(name, ver, arch)
    # accumulate cached files here
    acc = []
    # download multiple repos (os/updates) which will be coalesced later
    for n in Repositories.CENTOS_REPOS:
      # prepare request
      h, r, tmp = self._librepo_prepare(path)
      # point the request at CentOS os/updates repos
      h.mirrorlist = Repositories.CENTOS_METALINK_URL.format(ver, arch, n)

      try:
        h.perform(r)
      except librepo.LibrepoException as e:
        rc, msg, general_msg  = e
        print "Error: %s" % msg

      # read back the results
      data = r.getinfo(librepo.LRR_YUM_REPO)

      # cache the actual repo
      self._cache_db(data['filelists_db'], path, 'files-{}.sqlite'.format(n))
      self._cache_db(data['primary_db'], path, 'primary-{}.sqlite'.format(n))

      acc.extend([x.strip() for x in os.listdir(path)])
    return acc


  def create_repo_cache(self, name, ver, arch, typ=RepoType.Fedora):
    if typ == RepoType.Fedora:
      return self._cache_fedora(name, ver, arch)
    elif typ == RepoType.Centos:
      # need to download multiple repos and coalesce them at the sql handler level
      return self._cache_centos(name, ver, arch)
    else:
      raise ValueError("Unknown type: {}".format(typ))

class SqlHandler(object):
  _get_pkgid = 'SELECT `packages`.`pkgId`, `filelist`.`filenames` FROM `filelist`'\
               ' JOIN `packages` ON `packages`.`pkgKey` = `filelist`.`pkgKey`'\
               ' WHERE `dirname` =? AND `filenames` LIKE ?;'

  _get_pkgnevra = 'SELECT `name`, `epoch`, `version`, `release`, `arch` FROM `packages`'\
                  ' WHERE `arch` =? AND `pkgId` IN (%s)'\
                  ' ORDER BY `name` DESC;'

  def __init__(self, filelist, pkglist, **opt):
    self._pkglist = self._create_connections(pkglist)
    self._filelist = self._create_connections(filelist)
    # we need case sensitive `LIKE` statements
    self._sql_close(
      self._sql_execute_query(self._pkglist,
                              'PRAGMA case_sensitive_like = true;')
    )
    self._sql_close(
      self._sql_execute_query(self._filelist, 
                              'PRAGMA case_sensitive_like = true;')
    )
    if 'verbose' in opt:
      self._verbose = opt['verbose']

  @property
  def pkg(self):
    return self._pkglist

  @property
  def file(self):
    return self._filelist

  def _sql_execute_query(self, tgroup, query, *args):
    # execute the query for each target in target group and return result handles
    return [t.execute(query, *args) for t in tgroup]

  def _sql_close(self, queries):
    # close all queries
    return [q.close() for q in queries]

  def _sql_fetchall(self, queries):
    # fetch all results from the query in a flat array
    return [p for q in queries for p in q.fetchall()]

  def _sql_fetchone(self, queries):
    # fetch one unique result
    return set([q.fetchone() for q in queries]).pop()

  def _create_connections(self, targets):
    # connect to all target databases
    return [sqlite3.connect(x) for x in targets]

  def _format_sqlite_in(self, pkg_ids):
    return [x[0] for x in pkg_ids]

  def _format_package_nevra(self, nevra):
    if not nevra:
      return None
    return '{}-{}:{}-{}.{}'.format(*nevra)

  def get_package_for_include(self, include, arch):
    # this technically disallows searching for files
    # in root directory, but who cares
    if '/' not in include:
      return ''

    idir, ifile = include.rsplit('/', 1)

    # returns (ID, filenames) 
    pkg_ids = self._sql_fetchall(
      self._sql_execute_query(self.file,
          SqlHandler._get_pkgid,
          (idir, '%{}%'.format(ifile))
      )
    )
    # %foo% will match foo_bar too, so we need to split
    # the returned string with '/' which is dbs filenames
    # sepatartor and figure out if we have an exact match
    pkg_ids_matched = [pi for pi in pkg_ids 
                        if ifile in pi[1].split('/')]

    if app.debug and self._verbose:
      # figure out the eliminated IDs from the last step
      eliminated = "\n".join([x[0] for x in (set(pkg_ids) - set(pkg_ids_matched))])
      if eliminated:
        print("Eliminated non-exact matches:\n{}".format(
          eliminated
        ))

    # format the IDs for SQL IN statement
    inset = self._format_sqlite_in(pkg_ids_matched)
    # we also need to inject right amount of ?'s for prepared 
    # statement string substitution
    nevra = self._sql_fetchone(
      self._sql_execute_query(self.pkg,
          SqlHandler._get_pkgnevra % ','.join('?'*len(inset)),
          [arch] + inset
      )
    )
    if self._verbose and nevra:
      # return the package name as well as the include file that brought it in
      return "{} {}".format(self._format_package_nevra(nevra), include)

    return self._format_package_nevra(nevra)

  def process_includes(self, arch, includes):
    # process multiple includes and return unique results
    return filter(None, 
        set([self.get_package_for_include(inc, arch) for inc in includes])
    )

@app.route("/get_packages", methods=['POST'])
def get_includes():
  verbose = 'verbose' in request.args

  arch, name, release = get_args()
  base = os.path.join('cache', name, release, arch)

  # glob for db files, the glob will actually match multiple files
  # only for CentOS repositories, where the content is split 
  # between 'os' repo and 'updates' repo. While this is true for
  # Fedora repositories too (fedora.repo, fedora-updates.repo),
  # in Fedora the content of both of these repos is incremental, while
  # in CentOS ... excremental? :D What I mean is that 'os' doesn't contain
  # /usr/bin/python while 'updates' does, and there's more examples like this.
  sql = SqlHandler(glob.glob(os.path.join(base, 'files*.sqlite')),
                   glob.glob(os.path.join(base, 'primary*.sqlite')), 
                   verbose=verbose)

  if 'raw_includes' in request.form:
    # raw request from the HTML form
    # when in include mode we prepend include search paths before each element
    include_mode = False if 'include_mode' not in request.form else True
    includes = filter(None, request.form['raw_includes'].splitlines())
    if include_mode:
      # reuse these with feaders client search paths
      prefixes = ['/usr/include', '/usr/include/python2.7', '/usr/include/python3.4m']
      # combine the includes and prefixes
      includes = [os.path.join(p, i) for i in includes for p in prefixes]
    return '\n'.join(sql.process_includes(arch, includes))
  elif 'includes' in request.form:
    # JSON request, includes contains an array of include files to search for
    includes = json.loads(request.form['includes'])
    return json.dumps(sql.process_includes(arch, includes))
  else:
    return "Error, case unhandled"

@app.route("/add_cache")
def add_cache():
  return render_template('add_cache.html')

@app.route("/refresh_cache")
def refresh_cache():
  print('started caching')
  rh = RepoHandler('cache/')

  # get cache arguments
  arch, name, release = get_args()
  typ = RepoType.from_string(
    request.args.get('type', 'fedora')
  )

  # create cache
  caches = rh.create_repo_cache(
    name, release, arch, typ
  )

  if app.debug:
    # print the created caches in debug mode
    print("\n".join(caches))

  return redirect("/")

@app.route("/")
def index():
  seen, kv = set(), []
  # find the unique caches that we can use for searching
  for root, folder, files in os.walk('cache/'):
    for f in files:
      if f.startswith('primary') and f.endswith('sqlite'):
        kvs = zip(('name', 'release', 'arch'), root.split('/')[1:4])
        as_str = str(kvs)
        if as_str not in seen:
          seen.add(as_str)
          kv.append(dict(kvs))
  return render_template('index.html', cached=kv)

if __name__ == "__main__":
  app.run(debug=True, port=5000)
