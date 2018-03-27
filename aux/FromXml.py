#!/usr/bin/env python3
# This Source Code Form is licensed MPL-2.0: http://mozilla.org/MPL/2.0
import sys, re
from lxml import etree  # python3-lxml
import html
import Node

# produce stderr messages
def printerr (*args, **kwargs):
  print (*args, file = sys.stderr, **kwargs)

# check parsing an XML file
def parse_xml (xmlfile):
  if verbose:
    printerr ('  LOADING ', xmlfile)
  p = etree.XMLParser (huge_tree = True)
  tree = etree.parse (xmlfile, parser = p)
  return tree

class Data:
  def __init__ (self, node):
    self.node = node
    self.refid = Node.refid (node)
    self.name = Node.name (node)

class Function (Data):
  def __init__ (self, node):
    assert node.tag == 'memberdef'
    super().__init__ (node)
    self.refid = Node.get (node, 'id')
    assert self.refid
    self.rtype = Node.get (self.node, 'type')
    self.argstring = Node.get (self.node, 'argsstring')
    self.briefdescription = Node.get (self.node, 'briefdescription')
    self.detaileddescription = Node.get (self.node, 'detaileddescription')
  def description (self):
    t = self.briefdescription
    if t and self.detaileddescription:
      t += '\n'
    t += self.detaileddescription
    return t.strip()

class Compound (Data):
  def __init__ (self, xmldir, node):
    super().__init__ (node)
    self.outer = node
    self.xml_tree = parse_xml (xmldir + '/' + Node.refid (self.outer) + '.xml')
    root = self.xml_tree.getroot()
    assert root.tag == 'doxygen'
    cd = Node.first_child (root)
    assert cd != None and cd.tag == 'compounddef' and Node.kind (cd) == self.compound_kind
    self.node = cd
    assert Node.get (self.node, 'compoundname') == self.name
    self.functions = []
    for sub in self.node:
      if sub.tag == 'sectiondef':
        self.collect_members (sub)
  def collect_members (self, node):
    for m in Node.child_filter (node, 'memberdef'):
      if Node.kind (m) == 'function':
        self.functions += [ Function (m) ]

class Namespace (Compound):
  def __init__ (self, xmldir, node):
    self.compound_kind = 'namespace'
    super().__init__ (xmldir, node)
    self.anon = self.name and self.name[0] == '@'
  def has_docs (self):
    for f in self.functions:
      if f.description():
        return True
    return False

class File (Compound):
  def __init__ (self, xmldir, node):
    self.compound_kind = 'file'
    super().__init__ (xmldir, node)

# read XML
class DoxyParser:
  def __init__ (self, xmldir):
    self.xmldir = xmldir
    self.xml_tree = parse_xml (self.xmldir + '/index.xml')
    self.root = self.xml_tree.getroot()
    self.namespaces = []
    self.files = []
    self.collect (self.root)
  def collect (self, node):
    for c in Node.child_filter (node, 'compound'):
      if Node.kind (c) == 'namespace':
        if Node.name (c) == 'std':
          continue # ignore BUILTIN_STL_SUPPORT
        self.namespaces += [ Namespace (self.xmldir, c) ]
      if Node.kind (c) == 'file':
        self.files += [ File (self.xmldir, c) ]

# Usage: $0 xmldir/
xmldirs = []
verbose = False
none_ok = False
i = 1
while i < len (sys.argv):
  if sys.argv[i] == '--verbose':
    verbose = True
  elif sys.argv[i] == '--testxml' and i + 1 < len (sys.argv):
    i += 1
    parse_xml (sys.argv[i])
    none_ok = True
  else:
    xmldirs += [ sys.argv[i] ]
  i += 1

if not none_ok and len (xmldirs) < 1:
  raise RuntimeError ('missing XML dir argument')

def escape_types (string):
  string = re.sub (r'([*\\])', r'\\\1', string)
  return string

def mark_argstring (args, f = None):
  if len (args) < 2 or not args.startswith ('(') or not args.endswith (')'):
    return escape_types (args)
  inner = args[1:-1].strip()
  title = ''
  if f:
    title = ' title="' + html.escape (f.rtype + ' ' + f.name + ' ' + f.argstring) + '"'
  return '(<span class="args"' + title + '>' + escape_types (inner) + '</span>)'

def print_func (f):
  d = f.description()
  if d:
    print ('\n##', f.name, '() {-}')
    print ('<tt>', f.rtype, f.name, mark_argstring (f.argstring, f), '</tt> \\')
    print (d)

for xmldir in xmldirs:
  dp = DoxyParser (xmldir)
  if verbose:
    printerr ('  GEN     ', 'markdown docs')
  for n in dp.namespaces:
    if n.anon or not n.has_docs():
      continue
    print ('\n#', n.name)
    for f in n.functions:
      print_func (f)
  print ('\n#', '-GLOBALS-')
  for d in dp.files:
    for f in d.functions:
      print_func (f)
