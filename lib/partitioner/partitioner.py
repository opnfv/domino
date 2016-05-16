#!/usr/bin/env python

#
# Licence statement goes here
#

import constants 
import copy

def partition_tosca(filepath, nodesite, tpl):
  file_paths = {} #holds the list of partitioned files
  flag = {} #True when key exists
  sitenodes = {} #holds nodes in each site
  
  #identify the number of partitions
  for node in nodesite:
    if nodesite[node] != []:
     flag[nodesite[node]] = True
     if sitenodes.has_key(nodesite[node]):
       sitenodes[nodesite[node]].append(node)
     else:
       sitenodes[nodesite[node]] = [node]

  n_parts = len(flag)

  #prepare the nodes
  tpl_local = {}
  for site in sitenodes:
    tpl_local[site] = copy.deepcopy(tpl)  
  #remove the nodes not assigned to a site
  for node in nodesite:
   for site in sitenodes:
     if node not in sitenodes[site]:
       del tpl_local[site]['topology_template']['node_templates'][node] 
       #remove from policy targets 
       if tpl_local[site]['topology_template'].has_key('policies'):
         for rule in tpl_local[site]['topology_template']['policies']:
           for key in rule: #there should be only one key
             if node in rule[key]['targets']:
               rule[key]['targets'].remove(node)
             # remove the rule is there is no target left!
             if len(rule[key]['targets']) is 0:
               tpl_local[site]['topology_template']['policies'].remove(rule)

  for site in sitenodes:
    tpl_l = tpl_local[site]
    print tpl_l , '\n'
    file_paths[site] = filepath + '_part' + str(site)
    fout = open(filepath + '_part' + str(site),'w')
 
    if tpl_l.has_key('tosca_definitions_version'):
      fout.write('tosca_definitions_version: ')
      fout.write(tpl_l['tosca_definitions_version'] + '\n')    
      write_obj(fout, tpl_l['tosca_definitions_version'], None, '  ') 
   
    fout.write('\n')

    if tpl_l.has_key('description'):
       fout.write('description: ')
       fout.write(tpl_l['description'] + '\n')
       write_obj(fout, tpl_l['description'], None, '  ')

    fout.write('\n')

    if tpl_l.has_key('metadata'):
       fout.write('metadata: ' + '\n')
       write_obj(fout, tpl_l['metadata'], None, '  ')

    fout.write('\n')

    if tpl_l.has_key('policy_types'):
       fout.write('policy_types: ' + '\n')
       write_obj(fout, tpl_l['policy_types'], None, '  ')

    fout.write('\n')

    if tpl_l.has_key('topology_template'):
       fout.write('topology_template: ' + '\n')
       write_obj(fout, tpl_l['topology_template'], None, '  ')
   
    fout.close() 
  
  return file_paths


def write_obj(f, curr, prev, prepad):
  if type(curr) in (str,int,float,bool): 
    #should be a string, numerical, boolean, etc.
    if type(prev) is dict:
      #write on the same line, key should be written
      f.write(' ' + str(curr) + '\n')

  elif type(curr) is dict:
    if prev is not None and type(prev) is not list:
      f.write('\n')
    for key in curr:
        if type(prev) is list:
          f.write(prepad + '- ' + str(key) + ':')
          write_obj(f, curr[key], curr, prepad + '    ')
        else:
          f.write(prepad + str(key) + ':')
          write_obj(f, curr[key], curr, prepad + '  ')
  
  elif type(curr) is list:
    #check if this list is a leaf node
    if len(curr) is 0 or  type(curr[0]) in (str,int,float,bool):
      f.write(' ')
      f.write(str(curr).replace("'",""))
    #iterate over list of dictionaries
    f.write('\n') 
    for item in curr:
      write_obj(f, item, curr, prepad )
