#!/usr/bin/env python

#Copyright 2015 Open Platform for NFV Project, Inc. and its contributors
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
import sqlite3
#sys.path.append('gen-py')
#sys.path.insert(0, glob.glob('./lib/py/build/lib.*')[0])
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
    self.seqno = 0;
   
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
    except Thrift.TException, tx:
      logging.error('%s' , tx.message) 



  def closeconnection(self):
    self.transport.close()

  def push_template(self,template,ipaddr,tcpport):
    self.openconnection(ipaddr,tcpport)
    pushm = PushMessage()
    pushm.domino_udid = SERVER_UDID 
    pushm.seq_no = self.seqno
    pushm.template_type = 'tosca-nfv-v1.0'
    pushm.template = template
    try:
      push_r = self.sender.d_push(pushm)  
      logging.info('Push Response received from %d' , push_r.domino_udid)
    except (Thrift.TException, TSocket.TTransportException) as tx:
      logging.error('%s' , tx.message)
    except (socket.timeout) as tx:
      self.dominoServer.handle_RPC_timeout(pushm)
    except:       
      logging.error('Unexpected error: %s', sys.exc_info()[0])

    self.seqno = self.seqno + 1

    self.closeconnection()
 
  #Heartbeat from Domino Client is received
  #Actions:
  #	- Respond Back with a heartbeat

  def d_heartbeat(self, hb_msg):
    global SERVER_UDID
    logging.info('heartbeat received from %d' , hb_msg.domino_udid)

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
    global SERVER_UDID

    #Prepare and send Registration Response
    reg_r = RegisterResponseMessage()
    logging.info('Registration Request received for UDID %d from IP: %s port: %d', reg_msg.domino_udid_desired, reg_msg.ipaddr, reg_msg.tcpport)

   
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
    
    #commit to the database
    dbconn = sqlite3.connect(SERVER_DBFILE)
    c = dbconn.cursor()
    try:
      newrow = [(reg_r.domino_udid_assigned, reg_msg.ipaddr, reg_msg.tcpport, ','.join(reg_msg.supported_templates), reg_msg.seq_no),]
      c.executemany('INSERT INTO clients VALUES (?,?,?,?,?)',newrow)
    except sqlite3.OperationalError as ex:
      logging.error('Could not add the new registration record into %s for Domino Client %d :  %s', SERVER_DBFILE, reg_r.domino_udid_assigned, ex.message)
    except:
      logging.error('Could not add the new registration record into %s for Domino Client %d', SERVER_DBFILE, reg_r.domino_udid_assigned)
      logging.error('Unexpected error: %s', sys.exc_info()[0])
 
    dbconn.commit()
    dbconn.close()

    return reg_r


  #Subscription from Domino Client is received
  #Actions:
  #       - Save the templates  & labels
  #       - Respond Back with Subscription Response
  def d_subscribe(self, sub_msg):
    global SERVER_UDID, SERVER_SEQNO
    logging.info('Subscribe Request received from %d' , sub_msg.domino_udid)

    if sub_msg.template_op == APPEND:
      if self.dominoServer.subscribed_templateformats.has_key(sub_msg.domino_udid):
        self.dominoServer.subscribed_templateformats[sub_msg.domino_udid].update(set(sub_msg.supported_template_types))
      else:
        self.dominoServer.subscribed_templateformats[sub_msg.domino_udid] = set(sub_msg.supported_template_types)
    elif sub_msg.template_op == OVERWRITE:
      self.dominoServer.subscribed_templateformats[sub_msg.domino_udid] = set(sub_msg.supported_template_types)
    elif sub_msg.template_op == DELETE:
      self.dominoServer.subscribed_templateformats[sub_msg.domino_udid].difference_update(set(sub_msg.supported_template_types))

    if sub_msg.labels != []:
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
      c.execute("REPLACE INTO labels (udid, label_list) VALUES ({udid}, '{newvalue}')".\
               format(udid=sub_msg.domino_udid, newvalue=','.join(list(newlabelset)) ))
    except sqlite3.OperationalError as ex1:
      logging.error('Could not add the new labels to %s for Domino Client %d :  %s', SERVER_DBFILE, sub_msg.domino_udid, ex1.message)
    except:
      logging.error('Could not add the new labels to %s for Domino Client %d', SERVER_DBFILE, sub_msg.domino_udid)
      logging.error('Unexpected error: %s', sys.exc_info()[0])

    newttypeset = self.dominoServer.subscribed_templateformats[sub_msg.domino_udid]
    try:
      c.execute("REPLACE INTO ttypes (udid, ttype_list) VALUES ({udid}, '{newvalue}')".\
               format(udid=sub_msg.domino_udid, newvalue=','.join(list(newttypeset)) ))
    except sqlite3.OperationalError as ex1:
      logging.error('Could not add the new labels to %s for Domino Client %d :  %s', SERVER_DBFILE, sub_msg.domino_udid, ex1.message)
    except:
      logging.error('Could not add the new labels to %s for Domino Client %d', SERVER_DBFILE, sub_msg.domino_udid)
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
    global SERVER_UDID, SERVER_SEQNO, TOSCADIR, TOSCA_DEFAULT_FNAME
    logging.info('Publish Request received from %d' , pub_msg.domino_udid)
    logging.debug(pub_msg.template)

    # Save as file
    try:
      os.makedirs(TOSCADIR)
    except OSError as exception:
      if exception.errno == errno.EEXIST:
        logging.debug('ERRNO %d; %s exists. Creating: %s', exception.errno, TOSCADIR,  TOSCADIR+TOSCA_DEFAULT_FNAME)
      else:
        logging.error('Error occurred in creating %s. Err no: %d', exception.errno)

    #Risking a race condition if another process is attempting to write to same file
    f = open(TOSCADIR+TOSCA_DEFAULT_FNAME, 'w')  
    for item in pub_msg.template:
      print>>f, item
    f.close()

    # Load tosca object from file into memory
    tosca = ToscaTemplate( TOSCADIR+TOSCA_DEFAULT_FNAME )
    
    # Extract Labels
    node_labels = label.extract_labels( tosca )
    logging.debug('Node Labels: %s', node_labels)

    # Map nodes in the template to resource domains
    site_map = label.map_nodes( self.dominoServer.subscribed_labels , node_labels )
    logging.debug('Site Maps: %s' , site_map)

    # Select a site for each VNF
    node_site = label.select_site( site_map ) 
    logging.debug('Selected Sites: %s', node_site)

    # Create per-domain Tosca files
    file_paths = partitioner.partition_tosca('./toscafiles/template1.yaml',node_site,tosca.tpl)
    
    # Create list of translated template files

    # Create work-flow

    # Send domain templates to each domain agent/client 
    # FOR NOW: send untranslated but partitioned tosca files to scheduled sites
    # TBD: read from work-flow
    for site in file_paths:
      domino_client_ip = self.dominoServer.registration_record[site].ipaddr
      domino_client_port = self.dominoServer.registration_record[site].tcpport
      self.push_template(miscutil.read_templatefile(file_paths[site]), domino_client_ip, domino_client_port)

    #Fill in the details
    pub_r = PublishResponseMessage()
    pub_r.domino_udid = SERVER_UDID
    pub_r.seq_no = self.seqno
    pub_r.responseCode = SUCCESS
    self.seqno = self.seqno + 1 
    return pub_r
    
  #Query from Domino Client is received
  #Actions:
  #
  #       - Respond Back with Query Response
  def d_query(self, qu_msg):
    #Fill in the details
    qu_r = QueryResponseMessage()

    return qu_r


class DominoServer:
   def __init__(self):
     self.assignedUUIDs = list()
     self.subscribed_labels = dict()
     self.subscribed_templateformats = dict()
     self.registration_record = dict() 
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
     if udid_desired in self.assignedUUIDs:
       new_udid = random.getrandbits(63)
       while new_udid in self.assignedUUIDs:
         new_udid = random.getrandbits(63)
 
       self.assignedUUIDs.append(new_udid)
       return new_udid
     else:
       self.assignedUUIDs.append(udid_desired)
       return udid_desired
     
   def handle_RPC_timeout(self, RPCmessage):
     if RPCmessage.messageType == PUSH:
      logging.debug('RPC Timeout for message type: PUSH')
      # TBD: handle each RPC timeout separately

def main(argv):
  server = DominoServer()
  loglevel = LOGLEVEL
  #process input arguments
  try:
      opts, args = getopt.getopt(argv,"hc:l:",["conf=","log="])
  except getopt.GetoptError:
      print 'DominoServer.py -c/--conf <configfile> -l/--log <loglevel>'
      sys.exit(2)
  for opt, arg in opts:
      if opt == '-h':
         print 'DominoClient.py -c/--conf <configfile> -p/--port <socketport> -i/--ipaddr <IPaddr> -l/--log <loglevel>'
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
    c.execute('''CREATE TABLE labels (udid INTEGER PRIMARY KEY, label_list TEXT)''')
  except sqlite3.OperationalError as ex:
    logging.debug('In database file %s, no table is created as %s', SERVER_DBFILE, ex.message)

  try:
    c.execute('''CREATE TABLE ttypes (udid INTEGER PRIMARY KEY, ttype_list TEXT)''')
  except sqlite3.OperationalError as ex:
    logging.debug('In database file %s, no table is created as %s', SERVER_DBFILE, ex.message)

  try:
    c.execute('''CREATE TABLE clients (udid INTEGER PRIMARY KEY, ipaddr TEXT, tcpport INTEGER, templatetypes TEXT, seqno INTEGER)''')
  except sqlite3.OperationalError as ex:
    logging.debug('In database file %s, no table is created as %s', SERVER_DBFILE, ex.message)

  dbconn.commit()
  dbconn.close()

  logging.debug('Domino Server Starting...')
  server.start_communicationService()
  print 'done.'

if __name__ == "__main__":
   main(sys.argv[1:])
