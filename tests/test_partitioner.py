#!/usr/bin/env python

#Copyright 2016 Open Platform for NFV Project, Inc. and its contributors
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import sys, os, glob, yaml

sys.path.insert(0, glob.glob('./lib')[0])

#from toscaparser.tosca_template import ToscaTemplate

from mapper import *
from partitioner import *

def main():
  argv = sys.argv[1:]
  try:
    #tosca = ToscaTemplate(argv[0])
    tpl = yaml.load(file(argv[0],'r'))
    # Extract Labels
    node_labels = label.extract_labels( tpl )
    print node_labels
    site_id = 0
    subscribed_labels = {}
    for key in node_labels:
      subscribed_labels[site_id] = node_labels[key]
      site_id = site_id + 1

    # Map nodes in the template to resource domains
    site_map = label.map_nodes( subscribed_labels , node_labels )
    print site_map 

    # Select a site for each VNF
    node_site = label.select_site( site_map )
    print node_site

    tpl_site = {}
    file_paths = partitioner.partition_tosca("./tests/tmp/tosca",node_site,tpl,tpl_site)
    print file_paths

    boundary_VLs, VL_sites = partitioner.return_boundarylinks(tpl_site)
    print boundary_VLs
    print VL_sites

  except:
    print('Unexpected error: %s', sys.exc_info()[0])
    raise

if __name__ == "__main__":
  sys.exit(main())
