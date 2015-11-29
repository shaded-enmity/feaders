import librepo
import os
import shutil
import subprocess
import tempfile
import sys

def callback(data, total_to_download, downloaded):
  PROGRESSBAR_LEN = 30
  if total_to_download <= 0:
    return
  completed = int(downloaded / (total_to_download / PROGRESSBAR_LEN))
  sys.stdout.write("[%s%s] %8s/%8s (%s)\r" % ('#'*completed, 
                                   '-'*(PROGRESSBAR_LEN-completed), 
                                   int(downloaded), 
                                   int(total_to_download), 
                                   data))
  sys.stdout.flush()

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
