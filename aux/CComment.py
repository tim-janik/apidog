#!/usr/bin/env python3
# This Source Code Form is licensed MPL-2.0: http://mozilla.org/MPL/2.0
import os, sys, re, glob

# determine installation directory
qcommentfilter_dir = os.path.dirname (os.path.abspath (os.path.realpath (sys.argv[0])))
sys.path.append (qcommentfilter_dir)    # allow loading of modules from installation dir

def printerr (*args, **kwargs):
  print (*args, file = sys.stderr, **kwargs)

class CommentRegistry:
  def __init__ (self, seed = None):
    self.count = 0
    self.seed = seed
    self.comments = {}
  def add (self, comment_text, fname, fline):
    key = '____doxer_RegisteredComment_s%s_%u___' % (str (self.seed), 1 + len (self.comments))
    self.comments[key] = (comment_text, fname, fline)
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

# --- command line help ---
def print_help (with_help = True):
  print ("ccomment.py - helper for doxygen-xml")
  if not with_help:
    return
  print ("Usage: %s <inputdir> <outputdir>" % os.path.basename (sys.argv[0]))
  print ("Options:")
  print ("  --help, -h                print this help message")

# == globs ==
FILE_PATTERNS = [
      '*.c', '*.cc', '*.cxx', '*.cpp', '*.c++' '*.C', '*.CC', '*.Cpp', '*.CPP', '*.CXX', '*.C++',
      '*.h', '*.hh', '*.hxx', '*.hpp', '*.h++', '*.H', '*.HH', '*.Hpp', '*.HPP', '*.HXX', '*.H++',
      '*.java', '*.idl', '*.inc',
  ]

# --- filter all input ---
if len (sys.argv) < 3 or sys.argv[1] == '--help':
    print_help()
    sys.exit (0)

if 1: # <inputdir> <outputdir>
  inputdir = os.path.realpath (sys.argv[1])
  outputdir = sys.argv[2]
  comment_registry = CommentRegistry (0x0beef0c0ffe0aba0def)
  ilen = len (inputdir) + 1 # length to strip from input file names
  for g in FILE_PATTERNS:
    for f in glob.glob (os.path.join (inputdir, g)):
      assert len (f) > ilen
      out = os.path.join (outputdir, f[ilen:])
      printerr (f, out)
      fin = open (f, 'r')
      fout = open (out, 'w')
      ct = CommentTransformer (f, fin, fout, comment_registry)
      for lstr in fin:
        ct.feed_line (lstr)
      fin.close()
      fout.close()
  # --- dump comment registry ---
  with open (os.path.join (outputdir, '.ccomments.p'), 'wb') as ccp:
    comment_registry.flush (ccp)
