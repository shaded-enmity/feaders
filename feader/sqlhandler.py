import sqlite3

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
    # fetch one unique non-NULL result
    s = set(filter(None, [q.fetchone() for q in queries]))
    if not s:
      return None
    return s.pop()

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

    return self._format_package_nevra(nevra) if nevra else None

  def process_includes(self, arch, includes):
    # process multiple includes and return unique results
    return filter(None, 
        set([self.get_package_for_include(inc, arch) for inc in includes])
    )
