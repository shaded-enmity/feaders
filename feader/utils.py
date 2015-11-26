#!/usr/bin/python -tt

from graph.node import Node, FileNode

def endswith(s, pats):
  return any(s.endswith(p) for p in pats)

def create_graph(files):
  return Node(None)
