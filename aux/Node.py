# This Source Code Form is licensed MPL-2.0: http://mozilla.org/MPL/2.0
from lxml import etree  # python3-lxml


# create array holding the children of `node`
def children (node):
  return list (node.iterchildren())

# create iterator over children named by `tag`
def child_filter (node, tag):
  return list (node.iterchildren (tag))

def first_child (node):
  for c in node.iterchildren():
    return c
  return None

# find all descendants named `tag`
def find_descendants (node, tag):
  return list (node.getiterator (tag))

# find node or descendant named `tag`
def find (node, tag):
  if node.tag == tag:
    return node
  for child in node.getiterator (tag):
    return child
  return None

# Build a list of text strings contained in the subtree of `node`
def text_list (node):
  return node.xpath ("//text()") # lxml.etree only, returns [ 'TEXT', 'TAIL', ... ]

# Retrieve node contents as text
def text (node):
  return node.xpath ("string()") # lxml.etree only, returns 'TEXTTAIL'

# Retrieve text via key `tag` from an attribute or subtree
def get (node, tag):
  if tag in node.attrib:
    return node.attrib[tag]
  child = find (node, tag)
  return text (child) if child != None else ''

# convenience aliases
def kind (node):
  return get (node, 'kind')
def refid (node):
  return get (node, 'refid')
def name (node):
  return get (node, 'name')

