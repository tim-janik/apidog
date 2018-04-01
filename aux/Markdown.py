# This Source Code Form is licensed MPL-2.0: http://mozilla.org/MPL/2.0
import sys, re, os, json
import html

# produce stderr messages
def printerr (*args, **kwargs):
  print (*args, file = sys.stderr, **kwargs)

def compound (kind, name = None):
  if name == None:
    name = kind
    print ('\n#', name)
  else:
    print ('\n#', kind, name)

def typeclass (kind, name):
  print ('\n##', kind, name)

def member (name):
  print ('\n###', name, '{-}')

def tick_escape (string):
  string = re.sub (r'```', r'\`\`\`', string)
  return string

def prototype (prototext):
  print ('```{.mp-prototype}')
  print (tick_escape (prototext))
  print ('```')
