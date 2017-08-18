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

import sys, os, glob, random, errno
import getopt, socket
import logging, json
import sqlite3, yaml
import uuid

sys.path.insert(0, glob.glob('./lib')[0])


from dominoRPC import Communication
from dominoRPC.ttypes import *
from dominoRPC.constants import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

from toscaparser.tosca_template import ToscaTemplate
#from toscaparser.utils.gettextutils import _
#import toscaparser.utils.urlutils
from translator.hot.tosca_translator import TOSCATranslator


from mapper import *
from partitioner import *
from util import miscutil

#Load configuration parameters
from domino_conf import *


class CommunicationHandler:
  def __init__(self):
    self.log = {}

  def __init__(self, dominoserver):
    self.log = {}
    self.dominoServer = dominoserver
    self.seqno = SERVER_SEQNO;
   
  def openconnection(self, ipaddr, tcpport):
    try:
      # Make socket
      transport = TSocket.TSocket(ipaddr, tcpport)
      transport.setTimeout(THRIFT_RPC_TIMEOUT_MS)
      # Add buffering to compensate for slow raw sockets
      self.transport = TTransport.TBufferedTransport(transport)
      # Wrap in a protocol
      self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
      # Create a client to use the protocol encoder
      self.sender = Communication.Client(self.protocol)
      self.transport.open()
    except:
      raise


  def closeconnection(self):
    self.transport.close()

  def push_template(self,template,ipaddr,tcpport,TUID):
    try:
      self.openconnection(ipaddr,tcpport)
      pushm = PushMessage()
      pushm.domino_udid = SERVER_UDID 
      pushm.seq_no = self.seqno
      pushm.template_type = 'tosca-nfv-v1.0'
      pushm.template = template
      pushm.template_UUID = TUID
      self.seqno = self.seqno + 1

      push_r = self.sender.d_push(pushm)  
      logging.info('Push Response received from %s' , push_r.domino_udid)
      self.closeconnection()
    except (socket.timeout) as tx:
      self.dominoServer.handle_RPC_timeout(pushm)
      raise tx
    except:       
      logging.error('Unexpected error: %s', sys.exc_info()[0])
      raise
 
  #Heartbeat from Domino Client is received
  #Actions:
  #	- Respond Back with a heartbeat

  def d_heartbeat(self, hb_msg):
    logging.info('heartbeat received from %s' , hb_msg.domino_udid)

    hb_r = HeartBeatMessage()
    hb_r.domino_udid = SERVER_UDID
    hb_r.seq_no = self.seqno

    self.seqno = self.seqno + 1 

    return hb_r

  #Registration from Domino Client is received
  #Actions:
  #
  #       - Respond Back with Registration Response
  def d_register(self, reg_msg):

    #Prepare and send Registration Response
    reg_r = RegisterResponseMessage()
    logging.info('Registration Request received for UUID %s from IP: %s port: %d', reg_msg.domino_udid_desired, reg_msg.ipaddr, reg_msg.tcpport)

   
    reg_r.domino_udid_assigned = self.dominoServer.assign_udid(reg_msg.domino_udid_desired)
    reg_r.seq_no = self.seqno
    reg_r.domino_udid = SERVER_UDID
    #return unconditional success 
    #To be implemented:
    #Define conditions for unsuccessful registration (e.g., unsupported mapping)
    reg_r.responseCode = SUCCESS 
    #no need to send comments
    #To be implemented:
    #Logic for a new UDID assignment
 
    self.seqno = self.seqno + 1

    self.dominoServer.registration_record[reg_r.domino_udid_assigned] = reg_msg    

    #commit to the database
    dbconn = sqlite3.connect(SERVER_DBFILE)
    c = dbconn.cursor()
    try:
      newrow = [(reg_r.domino_udid_assigned, reg_msg.ipaddr, reg_msg.tcpport, ','.join(reg_msg.supported_templates), reg_msg.seq_no),]
      c.executemany('INSERT INTO clients VALUES (?,?,?,?,?)',newrow)
    except sqlite3.OperationalError as ex:
      logging.error('Could not add the new registration record into %s for Domino Client %s :  %s', SERVER_DBFILE, reg_r.domino_udid_assigned, ex.message)
    except:
      logging.error('Could not add the new registration record into %s for Domino Client %s', SERVER_DBFILE, reg_r.domino_udid_assigned)
      logging.error('Unexpected error: %s', sys.exc_info()[0])
 
    dbconn.commit()
    dbconn.close()

    return reg_r


  #Subscription from Domino Client is received
  #Actions:
  #       - Save the templates  & labels
  #       - Respond Back with Subscription Response
  def d_subscribe(self, sub_msg):
    logging.info('Subscribe Request received from %s' , sub_msg.domino_udid)

    if sub_msg.template_op == APPEND:
      if self.dominoServer.subscribed_templateformats.has_key(sub_msg.domino_udid):
        self.dominoServer.subscribed_templateformats[sub_msg.domino_udid].update(set(sub_msg.supported_template_types))
      else:
        self.dominoServer.subscribed_templateformats[sub_msg.domino_udid] = set(sub_msg.supported_template_types)
    elif sub_msg.template_op == OVERWRITE:
      self.dominoServer.subscribed_templateformats[sub_msg.domino_udid] = set(sub_msg.supported_template_types)
    elif sub_msg.template_op == DELETE:
      self.dominoServer.subscribed_templateformats[sub_msg.domino_udid].difference_update(set(sub_msg.supported_template_types))

#    if sub_msg.labels != []:
    if sub_msg.label_op == APPEND:
      logging.debug('APPENDING Labels...')
      if self.dominoServer.subscribed_labels.has_key(sub_msg.domino_udid):
	self.dominoServer.subscribed_labels[sub_msg.domino_udid].update(set(sub_msg.labels))
      else:
	self.dominoServer.subscribed_labels[sub_msg.domino_udid] = set(sub_msg.labels)
    elif sub_msg.label_op == OVERWRITE:
      logging.debug('OVERWRITING Labels...')
      self.dominoServer.subscribed_labels[sub_msg.domino_udid] = set(sub_msg.labels)
    elif sub_msg.label_op == DELETE:
      logging.debug('DELETING Labels...')
      self.dominoServer.subscribed_labels[sub_msg.domino_udid].difference_update(set(sub_msg.labels))

    logging.debug('Supported Template: %s Supported Labels: %s' , self.dominoServer.subscribed_templateformats[sub_msg.domino_udid] , self.dominoServer.subscribed_labels[sub_msg.domino_udid])

    #commit to the database
    dbconn = sqlite3.connect(SERVER_DBFILE)
    c = dbconn.cursor()
    newlabelset = self.dominoServer.subscribed_labels[sub_msg.domino_udid]
    try:
      newvalue=','.join(list(newlabelset))
      c.execute( "REPLACE INTO labels VALUES (?,?)", (sub_msg.domino_udid,newvalue) )
    except sqlite3.OperationalError as ex1:
      logging.error('Could not add the new labels to %s for Domino Client %s :  %s', SERVER_DBFILE, sub_msg.domino_udid, ex1.message)
    except:
      logging.error('Could not add the new labels to %s for Domino Client %s', SERVER_DBFILE, sub_msg.domino_udid)
      logging.error('Unexpected error: %s', sys.exc_info()[0])

    newttypeset = self.dominoServer.subscribed_templateformats[sub_msg.domino_udid]
    try:
      newvalue=','.join(list(newttypeset))
      c.execute( "REPLACE INTO ttypes VALUES (?,?)", (sub_msg.domino_udid,newvalue) )
    except sqlite3.OperationalError as ex1:
      logging.error('Could not add the new labels to %s for Domino Client %s :  %s', SERVER_DBFILE, sub_msg.domino_udid, ex1.message)
    except:
      logging.error('Could not add the new labels to %s for Domino Client %s', SERVER_DBFILE, sub_msg.domino_udid)
      logging.error('Unexpected error: %s', sys.exc_info()[0])


    dbconn.commit()
    dbconn.close()

 
    #Fill in the details
    sub_r = SubscribeResponseMessage()
    sub_r.domino_udid = SERVER_UDID
    sub_r.seq_no = self.seqno
    sub_r.responseCode = SUCCESS
    self.seqno = self.seqno + 1

    return sub_r

  #Template Publication from Domino Client is received
  #Actions:
  #       - Parse the template, perform mapping, partition the template
  #       - Launch Push service
  #       - Respond Back with Publication Response    
  def d_publish(self, pub_msg):
    logging.info('Publish Request received from %s' , pub_msg.domino_udid)
    #logging.debug(pub_msg.template)

    # Create response with response code as SUCCESS by default
    # Response code will be overwritten if partial or full failure occurs
    pub_r = PublishResponseMessage()
    pub_r.domino_udid = SERVER_UDID
    pub_r.seq_no = self.seqno
    pub_r.responseCode = SUCCESS
    pub_r.template_UUID = pub_msg.template_UUID
    self.seqno = self.seqno + 1

    if (pub_msg.template_UUID is not None) and (self.dominoServer.TUID2Publisher.has_key(pub_msg.template_UUID) == False):
      logging.debug('TEMPLATE UUID %s does not exist', pub_msg.template_UUID)
      pub_r.responseCode = FAILED
      return pub_r
      
    # Save as file
    try:
      os.makedirs(TOSCADIR)
    except OSError as exception:
      if exception.errno == errno.EEXIST:
        logging.debug('ERRNO %d; %s exists. Creating: %s', exception.errno, TOSCADIR,  TOSCADIR+TOSCA_DEFAULT_FNAME)
      else:
        logging.error('IGNORING error occurred in creating %s. Err no: %d', exception.errno)

    #Risking a race condition if another process is attempting to write to same file
    try:
      miscutil.write_templatefile(TOSCADIR+TOSCA_DEFAULT_FNAME , pub_msg.template)
    except:
      #Some sort of race condition should have occured that prevented the write operation
      #treat as failure
      logging.error('FAILED to write the published file: %s', sys.exc_info()[0])
      pub_r.responseCode = FAILED
      return pub_r
    
    # Load tosca object from file into memory
    try:
      #tosca = ToscaTemplate( TOSCADIR+TOSCA_DEFAULT_FNAME )
      tpl = yaml.load(file(TOSCADIR+TOSCA_DEFAULT_FNAME,'r'))
    except:
      logging.error('Tosca Parser error: %s', sys.exc_info()[0])
      #tosca file could not be read
      pub_r.responseCode = FAILED
      return pub_r 

    # Extract Labels
    node_labels = label.extract_labels( tpl )
    logging.debug('Node Labels: %s', node_labels)

    # Map nodes in the template to resource domains
    site_map = label.map_nodes( self.dominoServer.subscribed_labels , node_labels )
    logging.debug('Site Maps: %s' , site_map)

    # Select a site for each VNF
    node_site = label.select_site( site_map ) 
    logging.debug('Selected Sites: %s', node_site)

    # Create per-site Tosca files
    tpl_site = {}
    file_paths = partitioner.partition_tosca('./toscafiles/template',node_site,tpl,tpl_site)
    logging.debug('Per domain file paths: %s', file_paths)
    logging.debug('Per domain topologies: %s', tpl_site)
  
    # Detect boundary links
    boundary_VLs, VL_sites = partitioner.return_boundarylinks(tpl_site)
    logging.debug('Boundary VLs: %s', boundary_VLs)
    logging.debug('VL sites: %s', VL_sites)

    # Create work-flow

    # Assign template UUID if no UUID specified
    # Otherwise update the existing domains subscribed to TUID
    unsuccessful_updates = []
    if pub_msg.template_UUID is None:
      pub_r.template_UUID = self.dominoServer.assign_tuid() #update response message with the newly assigned template UUID
    else:
      logging.debug('TEMPLATE UUID %s exists, verify publisher and update subscribers', pub_msg.template_UUID)
      if self.dominoServer.TUID2Publisher[pub_msg.template_UUID] != pub_msg.domino_udid: #publisher is not the owner, reject
        logging.error('FAILED to verify publisher: %s against the publisher on record: %s', pub_msg.domino_udid, self.dominoServer.TUID2Publisher[pub_msg.template_UUID])
        pub_r.responseCode = FAILED
        return pub_r  
      else: #Template exists, we need to find clients that are no longer in the subscription list list
        TUID_unsubscribed_list = list(set(self.dominoServer.TUID2Subscribers[pub_r.template_UUID]) - set(file_paths.keys()))
        if len(TUID_unsubscribed_list) > 0:
          logging.debug('%s no longer host any nodes for TUID %s', TUID_unsubscribed_list, pub_r.template_UUID)
        # Send empty bodied templates to domains which no longer has any assigned resource
        template_lines = []
        for i in range(len(TUID_unsubscribed_list)):
          domino_client_ip = self.dominoServer.registration_record[TUID_unsubscribed_list[i]].ipaddr
          domino_client_port = self.dominoServer.registration_record[TUID_unsubscribed_list[i]].tcpport  
          try:
            self.push_template(template_lines, domino_client_ip, domino_client_port, pub_r.template_UUID)        
          except:       
            logging.error('Error in pushing template: %s', sys.exc_info()[0]) 
            unsuccessful_updates.append(TUID_unsubscribed_list[i])

    # The following template distribution is not transactional, meaning that some domains
    # might be successfull receiving their sub-templates while some other might not
    # The function returns FAILED code to the publisher in such situations, meaning that
    # publisher must republish to safely orchestrate/manage NS or VNF

    # Send domain templates to each domain agent/client 
    # FOR NOW: send untranslated but partitioned tosca files to scheduled sites
    # TBD: read from work-flow
    domainInfo = []
    for site in file_paths:
      domino_client_ip = self.dominoServer.registration_record[site].ipaddr
      domino_client_port = self.dominoServer.registration_record[site].tcpport
      domainInfo.append(DomainInfo(ipaddr=domino_client_ip,tcpport=domino_client_port))
      try:
        if 'hot' in self.dominoServer.subscribed_templateformats[site]:
          tosca = ToscaTemplate(file_paths[site])
          translator = TOSCATranslator(tosca, {}, False)
          output = translator.translate()
          logging.debug('HOT translation: \n %s', output)
          template_lines = [ output ]
        else: 
          template_lines = miscutil.read_templatefile(file_paths[site]) 
        self.push_template(template_lines, domino_client_ip, domino_client_port, pub_r.template_UUID)
      except IOError as e:
        logging.error('I/O error(%d): %s' , e.errno, e.strerror)
        pub_r.responseCode = FAILED
      except:
        logging.error('Error: %s', sys.exc_info()[0])
        pub_r.responseCode = FAILED

    # Check if any file is generated for distribution, if not
    # return FAILED as responseCode, we should also send description for
    # reason
    if len(file_paths) == 0:
      pub_r.responseCode = FAILED


    dbconn = sqlite3.connect(SERVER_DBFILE)
    c = dbconn.cursor()

    if pub_r.responseCode == SUCCESS:
      # send domain information only if all domains have received the domain templates
      pub_r.domainInfo = domainInfo
      # update in memory database
      self.dominoServer.TUID2Publisher[pub_r.template_UUID] = pub_msg.domino_udid
      try:
        c.execute( "REPLACE INTO templates VALUES (?,?)", (pub_r.template_UUID,pub_msg.domino_udid) )
        dbconn.commit()
      except sqlite3.OperationalError as ex1:
        logging.error('Could not add new TUID %s  DB for Domino Client %s :  %s', pub_r.template_UUID, pub_msg.domino_udid, ex1.message)
      except:
        logging.error('Could not add new TUID %s to DB for Domino Client %s', pub_r.template_UUID, pub_msg.domino_udid)
        logging.error('Unexpected error: %s', sys.exc_info()[0])
      else:
        self.dominoServer.TUID2Publisher[pub_r.template_UUID] = pub_msg.domino_udid

    # update in memory database
    self.dominoServer.TUID2Subscribers[pub_r.template_UUID] = list(set(unsuccessful_updates).union(set(file_paths.keys()))) #file_paths.keys()
    logging.debug('Subscribers: %s for TUID: %s', self.dominoServer.TUID2Subscribers[pub_r.template_UUID], pub_r.template_UUID)
    try:
      newvalue = ','.join(self.dominoServer.TUID2Subscribers[pub_r.template_UUID])
      c.execute( "REPLACE INTO subscribers VALUES (?,?)", (pub_r.template_UUID,newvalue) )
      dbconn.commit()
    except sqlite3.OperationalError as ex1:
      logging.error('Could not add new subscribers for TUID %s for Domino Client %s:  %s', pub_r.template_UUID, pub_msg.domino_udid, ex1.message)
    except:
      logging.error('Could not add new TUID %s to DB for Domino Client %s', pub_r.template_UUID, pub_msg.domino_udid)
      logging.error('Unexpected error: %s', sys.exc_info()[0])

    dbconn.close()

    return pub_r
    
  #Query from Domino Client is received
  #Actions:
  #
  #       - Respond Back with Query Response
  def d_query(self, qu_msg):
    #Fill in the details
    qu_r = QueryResponseMessage()
    qu_r.domino_udid = SERVER_UDID
    qu_r.seq_no = self.seqno
    qu_r.responseCode = SUCCESS
    qu_r.queryResponse = []
    
    for i in range(len(qu_msg.queryString)):
      if qu_msg.queryString[i] == 'list-tuids': # limit the response to TUIDs that belong to this domino client
         qu_r.queryResponse.extend([j for j in self.dominoServer.TUID2Publisher.keys() if self.dominoServer.TUID2Publisher[j] == qu_msg.domino_udid])

    self.seqno = self.seqno + 1
    return qu_r


class DominoServer:
   def __init__(self):
     self.assignedUUIDs = list()
     self.subscribed_labels = dict()
     self.subscribed_templateformats = dict()
     self.registration_record = dict() 
     self.assignedTUIDs = list()
     self.TUID2Publisher = dict()
     self.TUID2Subscribers = dict()
     self.communicationHandler = CommunicationHandler(self)
     self.processor = Communication.Processor(self.communicationHandler)
     self.transport = TSocket.TServerSocket(port=DOMINO_SERVER_PORT)
     self.tfactory = TTransport.TBufferedTransportFactory()
     self.pfactory = TBinaryProtocol.TBinaryProtocolFactory()
     #Use TThreadedServer or TThreadPoolServer for a multithreaded server
     #self.communicationServer = TServer.TThreadedServer(self.processor, self.transport, self.tfactory, self.pfactory)
     self.communicationServer = TServer.TThreadPoolServer(self.processor, self.transport, self.tfactory, self.pfactory)


   def start_communicationService(self):
     self.communicationServer.serve()

   #For now assign the desired UDID
   #To be implemented:
   #Check if ID is already assigned and in use
   #If not assigned, assign it
   #If assigned, offer a new random id
   def assign_udid(self, udid_desired):
     new_udid = udid_desired 
     while new_udid in self.assignedUUIDs:
       new_udid = uuid.uuid4().hex  
     self.assignedUUIDs.append(new_udid)
     return new_udid

   def assign_tuid(self):
     new_TUID = uuid.uuid4().hex
     while new_TUID in self.assignedTUIDs:
       new_TUID = uuid.uuid4().hex
     self.assignedTUIDs.append(new_TUID)  
     return new_TUID

   def handle_RPC_timeout(self, RPCmessage):
     if RPCmessage.messageType == PUSH:
      logging.debug('RPC Timeout for message type: PUSH')
      # TBD: handle each RPC timeout separately

def main():
  server = DominoServer()
  loglevel = LOGLEVEL
  #process input arguments
  try:
    opts, args = getopt.getopt(sys.argv[1:],"hc:l:",["conf=","log="])
  except getopt.GetoptError:
    print 'DominoServer.py -c/--conf <configfile> -l/--log <loglevel>'
    sys.exit(2)
  for opt, arg in opts:
      if opt == '-h':
         print 'DominoServer.py -c/--conf <configfile> -l/--log <loglevel>'
         sys.exit()
      elif opt in ("-c", "--conf"):
         configfile = arg
      elif opt in ("-l", "--log"):
         loglevel= arg
  #Set logging level
  numeric_level = getattr(logging, loglevel.upper(), None)
  try:
    if not isinstance(numeric_level, int):
      raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(filename=logfile,level=numeric_level, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
  except ValueError, ex:
    print ex.message
    sys.exit(2)

  #start the database with schemas
  dbconn = sqlite3.connect(SERVER_DBFILE)
  c = dbconn.cursor()
  try:
    c.execute('''CREATE TABLE labels (udid TEXT PRIMARY KEY, label_list TEXT)''')
  except sqlite3.OperationalError as ex:
    logging.debug('In database file %s, no table is created as %s', SERVER_DBFILE, ex.message)

  try:
    c.execute('''CREATE TABLE ttypes (udid TEXT PRIMARY KEY, ttype_list TEXT)''')
  except sqlite3.OperationalError as ex:
    logging.debug('In database file %s, no table is created as %s', SERVER_DBFILE, ex.message)

  try:
    c.execute('''CREATE TABLE clients (udid TEXT PRIMARY KEY, ipaddr TEXT, tcpport INTEGER, templatetypes TEXT, seqno INTEGER)''')
  except sqlite3.OperationalError as ex:
    logging.debug('In database file %s, no table is created as %s', SERVER_DBFILE, ex.message)

  try:
    c.execute('''CREATE TABLE templates (uuid_t TEXT PRIMARY KEY, udid TEXT)''')
  except sqlite3.OperationalError as ex:
    logging.debug('In database file %s, no table is created as %s', SERVER_DBFILE, ex.message)

  try:
    c.execute('''CREATE TABLE subscribers (tuid TEXT PRIMARY KEY, subscriber_list TEXT)''')
  except sqlite3.OperationalError as ex: 
    logging.debug('In database file %s, no table is created as %s', SERVER_DBFILE, ex.message)

  dbconn.commit()
  dbconn.close()

  logging.debug('Domino Server Starting...')
  server.start_communicationService()
  print 'done.'

if __name__ == "__main__":
  sys.exit(main())
