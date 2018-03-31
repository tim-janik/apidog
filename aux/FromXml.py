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
  p = etree.XMLParser (huge_tree = True)
  tree = etree.parse (xmlfile, parser = p)
  return tree

class Data:
  def __init__ (self, node):
    self.node = node
    self.refid = Node.refid (node)
    self.name = Node.name (node)
  def collect_data (self, node):
    self.briefdescription = Node.get (node, 'briefdescription').strip()
    self.detaileddescription = Node.get (node, 'detaileddescription').strip()
  def description (self):
    t = self.briefdescription
    if t and self.detaileddescription:
      t += '\n'
    t += self.detaileddescription
    return t.strip()

class Function (Data):
  def __init__ (self, node):
    assert node.tag == 'memberdef'
    super().__init__ (node)
    self.refid = Node.get (node, 'id')
    assert self.refid
    self.raw_type = Node.get (self.node, 'type')
    self.raw_argstring = Node.get (self.node, 'argsstring')
    self.collect_data (self.node)
  def argstring (self):
    s = self.raw_argstring
    s = re.sub (r'< +', '<', s)
    s = re.sub (r' +>', '>', s)
    return s
  def rtype (self):
    s = self.raw_type
    s = re.sub (r' *([*&])', r'\1', s)
    s = re.sub (r'< +', '<', s)
    s = re.sub (r' +>', '>', s)
    return s
  def has_docs (self):
    if self.briefdescription or self.detaileddescription:
      return True
    return False

class Compound (Data):
  def __init__ (self, xmldir, node):
    super().__init__ (node)
    self.outer = node
    self.xml_tree = parse_xml (xmldir + '/' + Node.refid (self.outer) + '.xml')
    root = self.xml_tree.getroot()
    assert root.tag == 'doxygen'
    cd = Node.first_child (root)
    assert cd != None and cd.tag == 'compounddef'
    if isinstance (self.compound_kind, str):
      assert Node.kind (cd) == self.compound_kind
    else:
      assert Node.kind (cd) in self.compound_kind
    self.node = cd
    self.collect_data (self.node)
    assert Node.get (self.node, 'compoundname') == self.name
    self.functions = []
    for sub in self.node:
      if sub.tag == 'sectiondef':
        self.collect_members (sub)
  def collect_members (self, node):
    for m in Node.child_filter (node, 'memberdef'):
      if Node.kind (m) == 'function':
        self.functions += [ Function (m) ]
  def has_docs (self):
    if self.briefdescription or self.detaileddescription:
      return True
    for f in self.functions:
      if f.has_docs():
        return True
    return False

class Namespace (Compound):
  def __init__ (self, xmldir, node):
    self.compound_kind = 'namespace'
    super().__init__ (xmldir, node)
    self.anon = self.name and self.name[0] == '@'

class File (Compound):
  def __init__ (self, xmldir, node):
    self.compound_kind = 'file'
    super().__init__ (xmldir, node)

class Class (Compound):
  compound_kind = ('class', 'struct', 'union', 'interface')
  def __init__ (self, xmldir, node, kind):
    self.compound_kind = kind
    super().__init__ (xmldir, node)

# read XML
class DoxyParser:
  def __init__ (self, xmldir):
    self.xmldir = xmldir
    self.xml_tree = parse_xml (self.xmldir + '/index.xml')
    self.root = self.xml_tree.getroot()
    self.namespaces = []
    self.files = []
    self.classes = []
    self.collect (self.root)
  def collect (self, node):
    for c in Node.child_filter (node, 'compound'):
      kind = Node.kind (c)
      if kind == 'namespace':
        if Node.name (c) == 'std':
          continue # ignore BUILTIN_STL_SUPPORT
        self.namespaces += [ Namespace (self.xmldir, c) ]
      elif kind == 'file':
        self.files += [ File (self.xmldir, c) ]
      elif kind in Class.compound_kind:
        self.classes += [ Class (self.xmldir, c, kind) ]
      else: # FIXME: class dir interface namespace struct union
        pass

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

def md_escape (string):
  string = re.sub (r'([*\\])', r'\\\1', string)
  return string
def hm_escape (string):
  return html.escape (md_escape (string))
def tick_escape (string):
  string = re.sub (r'```', r'\`\`\`', string)
  return string

def mark_argstring (args, f = None):
  if len (args) < 2 or not args.startswith ('(') or not args.endswith (')'):
    return hm_escape (args)
  inner = args[1:-1].strip()
  title = ''
  if f:
    title = ' title="' + hm_escape (f.rtype() + ' ' + f.name + ' ' + f.argstring()) + '"'
  return '(<span class="dmd-args"' + title + '>' + hm_escape (inner) + '</span>)'

def format_sections (t):
  # split off @param and @return
  arglist = re.split (r'\n[ \t]*(@(?:param|returns?)\b[^\n]*)', '\n' + t, re.M | re.I)
  params = []
  rets = []
  txts = []
  # sort and add markup
  for e in arglist:
    e = e.strip()
    if not e:
      continue
    m = re.match ('(@param)\s+(\w+)\s+(.+)', e)
    if m:
      params += [ '- **%s:** %s' % (m[2], m[3]) ]
      continue
    m = re.match ('(@returns?)\s+(.+)', e)
    if m:
      rets += [ '- **Returns:** %s' % m[2] ]
      continue
    else:
      txts += [ e ]
  # lists and para need newline separation
  if (params or rets) and txts:
    params = [ '<div class="dmd-arglead"></div>\n' ] + params
    txts = [ '\n' ] + txts
  # combine lines
  return '\n'.join (params + rets + txts) + '\n'

def print_func (f, prefix = ''):
  d = f.description()
  if d:
    prefix = prefix + '::' if prefix else prefix
    prefixed_name = f.name
    if prefix:
      prefixed_name = prefix.rstrip (':') + '.' + f.name
    print ('\n###', prefixed_name, '() {-}')
    print ('```{.dmd-prototype}')
    print (tick_escape (f.rtype()))
    print (f.name, '(', end = '')
    next_indent = ',\n ' + ' ' * len (f.name)
    argstring = f.argstring().strip()
    b = argstring.rfind (')')
    if b > 0:
      argstring, postfix = argstring[:b], argstring[b:]
    else:
      postfix = ')'
    if argstring.startswith ('(') and argstring.endswith (')'):
      argstring = argstring[1:-1].strip()
    if argstring.startswith ('('):
      argstring = argstring[1:]
    args = argstring.split (',')
    l = len (args)
    for i in range (l):
      t = next_indent if i else ''
      t += tick_escape (args[i])
      print (t, end = '')
    print ('%s;' % postfix)
    print ('```')
    print (format_sections (d))

for xmldir in xmldirs:
  if verbose:
    printerr ('  GEN     ', 'markdown docs')
  dp = DoxyParser (xmldir)
  for n in dp.namespaces:
    if n.anon or not n.has_docs():
      continue
    print ('\n# Namespace ', n.name)
    print (format_sections (n.description()))
    print ('\n##', n.name, 'Functions')
    for f in n.functions:
      print_func (f)
  print ('\n#', 'Global Symbols')
  print ('\n##', 'Global', 'Functions')
  for i in dp.files:
    for f in i.functions:
      print_func (f)
  for c in dp.classes:
    if not c.has_docs():
      continue
    print ('\n##', c.compound_kind.title(), c.name)
    print (format_sections (c.description()))
    for f in c.functions:
      print_func (f, c.name)
