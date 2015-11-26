#!/usr/bin/python -tt

class Node(object):
  def __init__(self, parent):
    self._parent = parent
    self._children = []

  @property
  def children(self):
    return self._children

  @property
  def parent(self):
    return self._parent

class FileNode(Node):
  def __init__(self, parent):
    super(FileNode, self).__init__(parent)
    self._path = ''
    self._includes = set()

  @property
  def path(self):
    return self._path

  @property
  def includes(self):
    return self._includes

  def get_all_includes(self):
    a = set(self._includes)
    for c in self.children:
      a += c.get_all_includes()
    return a
