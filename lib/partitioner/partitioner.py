#!/usr/bin/env python

#
# Licence statement goes here
#

import constants 
import copy

def partition_tosca(filepath, nodesite, tpl):
  file_paths = {} #holds the list of partitioned files
  sitenodes = {} #holds nodes in each site
  
  #identify the number of partitions
  for node in nodesite:
    if nodesite[node] != []:
     if sitenodes.has_key(nodesite[node]):
       sitenodes[nodesite[node]].append(node)
     else:
       sitenodes[nodesite[node]] = [node]

  #prepare the nodes
  tpl_local = {}
  for site in sitenodes:
    tpl_local[site] = copy.deepcopy(tpl)  
  #remove the nodes not assigned to a site
  for node in nodesite:
   for site in sitenodes:
     if node not in sitenodes[site]:
       tpl_local[site]['topology_template']['node_templates'].pop(node,None) 
       rm_dependents(tpl_local[site]['topology_template']['node_templates'] , node)
       #remove from policy targets 
       if tpl_local[site]['topology_template'].has_key('policies'):
         for rule in tpl_local[site]['topology_template']['policies']:
           for key in rule: #there should be only one key
             if node in rule[key]['targets']:
               rule[key]['targets'].remove(node)
             # remove the rule if there is no target left!
             if len(rule[key]['targets']) is 0:
               tpl_local[site]['topology_template']['policies'].remove(rule)
 
  for site in sitenodes:
    tpl_l = tpl_local[site]
    rm_orphans(tpl_l)
    file_paths[site] = filepath + '_part' + str(site) + '.yaml'
    fout = open(file_paths[site],'w')
 
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

def rm_dependents(node_template , node):
  del_list = []
  #find the dependents
  for nd in node_template:
    if node_template[nd].has_key('requirements'):
      for i in range(len(node_template[nd]['requirements'])):
        if node_template[nd]['requirements'][i].has_key('virtualLink') and \
          node_template[nd]['requirements'][i]['virtualLink'].has_key('node') and \
          node_template[nd]['requirements'][i]['virtualLink']['node'] == node:
          del_list.append(nd)
        if node_template[nd]['requirements'][i].has_key('virtualBinding') and \
          node_template[nd]['requirements'][i]['virtualBinding'].has_key('node') and \
          node_template[nd]['requirements'][i]['virtualBinding']['node'] == node:
          del_list.append(nd)
  #remove the dependents
  for i in range(len(del_list)):
     del node_template[del_list[i]]

def rm_orphans(tpl):
  nodes = tpl['topology_template']['node_templates']
  keep_list = []
  for node in nodes:
    if nodes[node].has_key('requirements'):
      for i in range(len(nodes[node]['requirements'])):
        if nodes[node]['requirements'][i].has_key('virtualLink'):
          keep_list.append(nodes[node]['requirements'][i]['virtualLink']['node'])
  for node in list(nodes):   
    if (nodes[node]['type'] == 'tosca.nodes.nfv.VL') and (node not in keep_list):
      del nodes[node]
