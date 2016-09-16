#!/usr/bin/env humblepy
import os

from libraries.aetycoon.prettydata import prettify
from sotb_displayitem import SOTBDisplayItem


def write_pretty_file(content, filename):
  """
  Writes a dictionarys to a new .py file on the users Desktop

  Args:
    content  (dict/list): A python dictionary or list.
    filename       (str): The name of the .py file created
  """
  output_directory = os.path.expanduser('~/Desktop/')
  with open(os.path.join(output_directory, '%s.py' % filename), 'wb') as f:
    if isinstance(content, dict):
      f.write(''.join(prettify(content)))
    elif isinstance(content, list):
      f.write('[\n')
      for c in content:
        if isinstance(c, SOTBDisplayItem):
          f.write(''.join(prettify(c.di_dict)))
        else:
          f.write(''.join(prettify(c)))
        f.write('\n,\n')
      f.write(']')
    else:
      print "Invalid content type. Please try again with a list or dict."
  print "%s.py has been created" % filename
