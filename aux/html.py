# This Source Code Form is licensed MPL-2.0: http://mozilla.org/MPL/2.0
import re, copy

def escape (string):
  string = re.sub ('&', '&amp;', string)
  string = re.sub ('<', '&lt;', string)
  string = re.sub ('>', '&gt;', string)
  string = re.sub ("'", '&apos;', string)
  string = re.sub ('"', '&quot;', string)
  return string

# Generator class for Html TOC lists.
class TocTree:
  def __init__ (self, soup):
    self.soup = soup
    self.root = self.soup.new_tag ('div', id = 'TOC')
    self.root.append ('\n')
    self.level = [ 0 ]
    self.stack = [ self.root ]
  def push (self, hx):
    n = int (hx.name[1])
    if n > self.level[-1]:
      ul = self.soup.new_tag ('ul')
      if self.stack[-1].name == 'ul':
        self.stack[-1].contents[-1].append ('\n')
        self.stack[-1].contents[-1].append (ul)
      else:
        self.stack[-1].append (ul)
      self.stack += [ ul ]
      self.level += [ n ]
    while n < self.level[-1]:
      self.level.pop()
      self.stack.pop()
    li = self.soup.new_tag ('li')
    a = self.soup.new_tag ('a')
    a['href'] = '#' + hx['id']
    #a['old'] = hx.name
    for c in hx.children:
      c = copy.copy (c)
      if c.name:
        classes = c.get ('class')
        if 'header-section-number' in classes:
          classes[classes.index ('header-section-number')] = 'toc-section-number'
      a.append (c)
    li.append (a)
    ul = self.stack[-1]
    assert ul.name == 'ul'
    ul.append ('\n')
    ul.append (li)

# Scan Html text for h1-h6 headings with anchors.
def scan_toc_headings (soup):
  l = []
  # in this soup of HTML elements
  for tag in soup.body.next_elements:
    # find headings
    if tag.name and tag.name.lower() in ('h1', 'h2',  'h3', 'h4', 'h5', 'h6'):
      h = copy.copy (tag)
      if not h.has_attr ('id'):
        if (tag.parent.name == 'div' and tag.parent.has_attr ('id') and
            'section' in tag.parent.get ('class',[])):
          h['id'] = tag.parent['id']  # add section-div anchor to heading if needed
        else:
          continue                      # or discard headings without anchors
      l.append (h)
  return l

# Generate a TOC from headings found in `html_files`.
def gen_toc (html_files):
  from bs4 import BeautifulSoup
  for hf in html_files:
    fin = open (hf, 'r')
    soup = BeautifulSoup (fin.read(), 'html.parser')
    del fin
    toctree = TocTree (soup)
    for hx in scan_toc_headings (soup):
      toctree.push (hx)
    return str (toctree.root)
