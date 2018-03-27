#!/usr/bin/env python3
# This Source Code Form is licensed MPL-2.0: http://mozilla.org/MPL/2.0
import os, sys, re, glob
import html

# determine installation directory
qcommentfilter_dir = os.path.dirname (os.path.abspath (os.path.realpath (sys.argv[0])))
sys.path.append (qcommentfilter_dir)    # allow loading of modules from installation dir

def printerr (*args, **kwargs):
  print (*args, file = sys.stderr, **kwargs)

comment_pattern = r'(\$ccomment\.py:[0-9a-f]+-[0-9]+\$)'

class CommentRegistry:
  def __init__ (self, seed = None):
    self.count = 0
    self.seed = seed
    self.comments = {}
  def add (self, comment_text, fname, fline):
    key = '$ccomment.py:%s-%u$' % (self.seed, 1 + len (self.comments)) # MUST match comment_pattern
    self.comments[key] = comment_text # FIXME: (comment_text, fname, fline)
    return key
  def flush (self, file):
    import pickle
    pickle.dump (self.comments, file)

class CommentTransformer:
  def __init__ (self, fname, fin, fout, cregistry):
    self.fin = fin
    self.fout = fout
    self.fname = fname
    self.buffer = '/** @file '+fname+' */ '
    self.cbuffer = ''
    self.feed_specific = self.feed_text
    self.cregistry = cregistry
    self.fline = 1
    self.start_line = 0
  def feed_text (self, char):
    self.buffer += char
    if char == '*' and self.buffer[-3:] in ('/**', '/*!'):
      self.start_line = self.fline
      self.feed_specific = self.feed_ccomment
    elif char == '<' and self.buffer[-4:] in ('///<', '//!<'):
      self.start_line = self.fline
      self.feed_specific = self.feed_scomment
    #elif char == '<' and self.buffer[-3:] == '/*<':
    #  self.buffer[-1] = '*'
    #  self.buffer += '<'        # for doxygen, fake '/**<' from  '/*<'
    #  self.start_line = self.fline
    #  self.feed_specific = self.feed_ccomment
    #elif char == '<' and self.buffer[-3:] == '//<':
    #  self.buffer[-1] = '/'
    #  self.buffer += '<'        # for doxygen, fake '///<' from  '//<'
    #  self.start_line = self.fline
    #  self.feed_specific = self.feed_scomment
    elif char == '\n':
      self.fout.write (self.buffer)
      self.buffer = ''
  def feed_ccomment (self, char):
    if not self.cbuffer and char == '<':
      self.buffer += '<'        # leave '/**<' and  '/*!<' comments intact
      return
    self.cbuffer += char
    if char == '\n':
      self.buffer += '\n'
    elif char == '/' and self.cbuffer[-2:] == '*/':
      self.buffer += ' ' + self.cregistry.add (self.cbuffer[:-2], self.fname, self.start_line) + ' '
      self.buffer += '*/'
      self.feed_specific = self.feed_text
      self.cbuffer = ''
  def feed_scomment (self, char):
    self.cbuffer += char
    if char == '\n':
      self.buffer += ' ' + self.cregistry.add (self.cbuffer[:-1], self.fname, self.start_line) + ' '
      self.buffer += '\n'
      self.feed_specific = self.feed_text
      self.cbuffer = ''
  def feed (self, char):
    self.feed_specific (char)
  def feed_line (self, lstr):
    for c in lstr:
      self.feed (c)
    self.fline += 1

# == globs ==
FILE_PATTERNS = [
      '*.c', '*.cc', '*.cxx', '*.cpp', '*.c++' '*.C', '*.CC', '*.Cpp', '*.CPP', '*.CXX', '*.C++',
      '*.h', '*.hh', '*.hxx', '*.hpp', '*.h++', '*.H', '*.HH', '*.Hpp', '*.HPP', '*.HXX', '*.H++',
      '*.java', '*.idl', '*.inc',
  ]


def restore (xmldir, db):
  import pickle
  comments = pickle.load (open (db, 'rb'))
  def lookup (s):
    if not s in comments:
      return s
    return html.escape (comments[s])
  for f in glob.glob (os.path.join (xmldir, '*.xml')):
    with open (f, 'r') as fin:
      parts = re.split (comment_pattern, fin.read())
      fin.close()
    if verbose:
      printerr ('  RESTORE ', f, len (parts))
    restored = map (lambda x: lookup (x), parts)
    with open (f, 'w') as fout:
      for s in restored:
        fout.write (s)
      fout.close()
    del parts

def store (sourcedir, codedir, commentdb):
  sourcedir = os.path.realpath (sourcedir)
  comment_registry = CommentRegistry ('bb3f3a813d33943f7650097038c3713359a')
  ilen = len (sourcedir) + 1 # length to strip from input file names
  for g in FILE_PATTERNS:
    for f in glob.glob (os.path.join (sourcedir, g)):
      assert len (f) > ilen
      out = os.path.join (codedir, f[ilen:])
      if verbose:
        printerr ('  STORE   ', f) # out
      fin = open (f, 'r')
      fout = open (out, 'w')
      ct = CommentTransformer (f, fin, fout, comment_registry)
      for lstr in fin:
        ct.feed_line (lstr)
      fin.close()
      fout.close()
  with open (commentdb, 'wb') as cdb:
    comment_registry.flush (cdb)

def print_help (with_help = True):
  print ("%s - helper for doxygen-xml" % os.path.basename (sys.argv[0]))
  if not with_help:
    return
  print ('Usage: %s [OPTIONS] {--store sourcedir builddir|--restore builddir destdir}' % os.path.basename (sys.argv[0]))
  print ("Options:")
  print ("  --verbose                 print processing information")
  print ("  --help                    print this help message")

# parse args, see Usage
verbose = False
i = 1
while i < len (sys.argv):
  if sys.argv[i] == '--verbose':
    verbose = True
  elif sys.argv[i] == '--restore' and i + 2 < len (sys.argv):
    i += 1
    codedir = sys.argv[i]
    i += 1
    xmldir = sys.argv[i]
    restore (xmldir, os.path.join (codedir, '.ccomments.p'))
  elif sys.argv[i] == '--store' and i + 2 < len (sys.argv):
    i += 1
    sourcedir = sys.argv[i]
    i += 1
    codedir = sys.argv[i]
    store (sourcedir, codedir, os.path.join (codedir, '.ccomments.p'))
  elif sys.argv[i] == '--help':
    print_help()
    sys.exit (0)
  else:
    raise RuntimeError ('argument not recognized: ' + sys.argv[i])
  i += 1
