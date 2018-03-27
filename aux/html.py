# This Source Code Form is licensed MPL-2.0: http://mozilla.org/MPL/2.0
import re

def escape (string):
  string = re.sub ('&', '&amp;', string)
  string = re.sub ('<', '&lt;', string)
  string = re.sub ('>', '&gt;', string)
  string = re.sub ("'", '&apos;', string)
  string = re.sub ('"', '&quot;', string)
  return string
