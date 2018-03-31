#!/usr/bin/env python3
# This Source Code Form is licensed MPL-2.0: http://mozilla.org/MPL/2.0
import sys, re, os, json
import html

# produce stderr messages
def printerr (*args, **kwargs):
  print (*args, file = sys.stderr, **kwargs)

# Usage: $0 jsdocoutput.json
jsonfiles = []
verbose = False
none_ok = False
i = 1
while i < len (sys.argv):
  if sys.argv[i] == '--verbose':
    verbose = True
  else:
    jsonfiles += [ sys.argv[i] ]
  i += 1
if not none_ok and len (jsonfiles) < 1:
  raise RuntimeError ('missing json file argument')

class File:
  def __init__ (self, filename):
    self.filename = filename
    self.functions = []

class Function:
  def __init__ (self, file, name, params = []):
    self.file = file
    self.name = name
    self.params = params
    self.longname = ''
    self.comment = ''
  def long (self):
    return self.longname if self.longname else self.name
  def module_name (self):
    f = os.path.basename (self.file.filename)
    return re.sub (r'\..*', '.', f) + self.long()
  def description (self):
    c = self.comment
    c = re.sub (r'^/\*+\s', '\n', c)   # strip starting comment markers
    c = re.sub (r'\s*\*+/$', '\n', c)  # strip trailing comment marker
    c = re.sub (r'\n ?\*+ ?', '\n', c) # strip leading comment asterisks for the following lines
    return c

class Jdoc:
  def __init__ (self):
    self.files = {}
  def get_file (self, filename, filepath):
    fp = os.path.join (filepath, filename)
    if fp not in self.files:
      self.files[fp] = File (fp)
    return self.files[fp]
  def add (self, e):
    if e['kind'] == 'function':
      meta = e['meta']
      fi = self.get_file (meta['filename'], meta['path'])
      code = meta['code']
      ctype = code['type']
      params = [ '...' ] # wierd default, because jsdoc@3.5.5 + jsdoc-json@2.0.2 fail to parse params for 'const ArrowFunctionExpression = (...) => {};'
      if 'paramnames' in code:
        params = code['paramnames']
      f = Function (fi, e['name'], params)
      fi.functions += [ f ]
      if 'longname' in e:
        f.longname = e['longname']
      if 'comment' in e:
        f.comment = e['comment']

for jf in jsonfiles:
  if verbose:
    printerr ('  GEN     ', 'markdown docs')
  root = json.loads (open (jf, "r").read())
  jd = Jdoc()
  if 'docs' in root:
    for e in root['docs']:
      jd.add (e)
  input_files = [fi.filename for fi in jd.files.values()]
  stripdir = html.common_dir (input_files) if len (input_files) != 1 else input_files[0]
  s = len (stripdir)
  for fi in jd.files.values():
    stripped_filename = fi.filename[s:]
    print ('\n# Module', stripped_filename)
    print ('\n##', stripped_filename, 'Functions')
    for f in fi.functions:
      print ('\n### ', f.module_name(), '() {-}')
      print ('```{.dmd-prototype}')
      # print (f.name, '(%s);' % (',\n  ' + ' ' * len (f.name)).join (f.params))
      print (f.name, '(%s);' % re.sub (r'(.{20}), ', r'\1,\n  ' + len (f.name) * ' ', ', '.join (f.params)))
      print ('```')
      d = f.description()
      if d:
        print (re.sub (r'^', '', d.strip(), flags = re.M))
