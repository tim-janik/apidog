# This Source Code Form is licensed MPL-2.0: http://mozilla.org/MPL/2.0
import sys, re, os, json
import html

# produce stderr messages
def printerr (*args, **kwargs):
  print (*args, file = sys.stderr, **kwargs)

# Generate a markdown heading for File / Module / Namespace compounds
def compound (kind, name = None):
  if name == None:
    name = kind
    print ('\n#', name)
  else:
    print ('\n#', kind, name)

# Generate a markdown heading for Objects / Function Sets / Variable Sets
def typeclass (kind, name):
  print ('\n##', kind, name)

# Generate a markdown heading for the constituting parts of a typeclass
def member (name):
  print ('\n###', name, '{-}')

def tick_escape (string):
  string = re.sub (r'```', r'\`\`\`', string)
  return string

# Generate a markdown code block for function prototypes
def prototype (prototext):
  print ('```{.mp-prototype}')
  print (tick_escape (prototext))
  print ('```')

# Convert @param and @return command to a markdown list
def description (description):
  # split off @param and @return
  arglist = re.split (r'\n[ \t]*(@(?:param|returns?)\b[^\n]*)', '\n' + description.strip(), re.M | re.I)
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
    params = [ '<div class="mp-arglead"></div>\n' ] + params
    txts = [ '\n' ] + txts
  # combine lines
  print ('\n'.join (params + rets + txts))
