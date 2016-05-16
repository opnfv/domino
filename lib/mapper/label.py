#!/usr/bin/env python

#
# Licence statement goes here
#

#from toscaparser.tosca_template import ToscaTemplate

#Current version:
#Parses policy rules, extracts targets, extracts policy properties
#Returns set of policy properties for each target in a dictionary object
#e.g., node_labels['VNF1'] = {label1, label2, ..., labeln}
def extract_labels(tosca):
  node_labels = dict() #stores labels for each node
  
  if tosca.tpl.has_key('topology_template'):
    if tosca.tpl['topology_template'].has_key('policies'):
      policies = tosca.tpl['topology_template']['policies']
    else:
      return node_labels
  else:
    return node_labels

  #extract label sets for each policy target
  for p in policies:
    for rule in p:
      targetlist = p[rule]['targets']
      for props in p[rule]['properties']:
        prop_list = p[rule]['properties'][props]
        for values in prop_list:
          labelkey = p[rule]['type']+ ':properties:' + props + ":" + values
          for target in targetlist:
            if node_labels.has_key(target):
              node_labels[target].update(set([labelkey]))
            else:
              node_labels[target] = set([labelkey])
  return node_labels

# Returns a map from nodes to regions based on label matching
def map_nodes(site_labels,node_labels):
  sitemap = dict() #stores mapping

  #for each target find a map of sites
  for node in node_labels:
    sitemap[node] = set()
    for site in site_labels:
      if node_labels[node].issubset(site_labels[site]):
        sitemap[node].add(site)

  return sitemap

# Selects sites for nodes if multiple candidates exist
# First iterate for nodes with single candidate site
# Rank sites with most nodes higher
def select_site( site_map ): 
  node_site = dict()
  counter = dict()
  #SHALL I CHECK IF ANY KEY HAS AN EMPTY SET TO THROW EXCEPTION?
  #For now, I assume input as safe

  for node in site_map:
    node_site[node] = [] 
    if len(site_map[node]) == 1:
      for site in site_map[node]:
        node_site[node] = site
        if counter.has_key(site):
          counter[site] = counter[site] + 1
        else:
          counter[site] = 1

  for node in site_map:
    if len(site_map[node]) > 1:
      maxval = 0
      maxkey = '-1'
      for site in site_map[node]:
        if counter.has_key(site) and counter[site] >= maxval:
          maxval = counter[site]
          maxkey = site
        elif counter.has_key(site) == False:
          counter[site] = 1
          if maxval == 0:
            maxval = 1
            maxkey = site
      node_site[node] = maxkey        
  return node_site 
