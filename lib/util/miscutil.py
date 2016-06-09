#!/usr/bin/env python

#
# Licence statement goes here
#

def read_templatefile(temp_filename): 
  f = open(temp_filename, 'r')
  lines = f.read().splitlines()
  f.close()
  return lines

def write_templatefile(temp_filename, template_lines):    
  f = open(temp_filename, 'w')
  for item in template_lines:
      print>>f, item
  f.close()
