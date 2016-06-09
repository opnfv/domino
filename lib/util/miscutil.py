#!/usr/bin/env python

#
# Licence statement goes here
#

def read_templatefile(temp_filename): 
  f = open(temp_filename, 'r')
  lines = f.read().splitlines()
  f.close()
  return lines

