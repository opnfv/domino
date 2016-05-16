#!/usr/bin/env python

#
# Licence statement goes here
#


import sys, os, glob, random, errno
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

SERVER_UDID = 0
DOMINO_CLIENT_IP = 'localhost'
DOMINO_CLIENT_PORT = 9091
TOSCADIR = './toscafiles/'
TOSCA_DEFAULT_FNAME = 'template1.yaml'

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
      # Add buffering to compensate for slow raw sockets
      self.transport = TTransport.TBufferedTransport(transport)
      # Wrap in a protocol
      self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
      # Create a client to use the protocol encoder
      self.sender = Communication.Client(self.protocol)
      self.transport.open()
    except Thrift.TException, tx:
      print '%s' % (tx.message) 


  def closeconnection(self):
    self.transport.close()

  def push_template(self,template,ipaddr,tcpport):
    global SERVER_UDID
    self.openconnection(ipaddr,tcpport)
    pushm = PushMessage()
    pushm.domino_udid = SERVER_UDID 
    pushm.seq_no = self.seqno
    pushm.template_type = 'tosca-nfv-v1.0'
    pushm.template = template

    push_r = self.sender.d_push(pushm)  

    print 'Push Response received from %d' % push_r.domino_udid 
    self.seqno = self.seqno + 1

    self.closeconnection()
 
  #Heartbeat from Domino Client is received
  #Actions:
  #	- Respond Back with a heartbeat

  def d_heartbeat(self, hb_msg):
    global SERVER_UDID
    print 'heart beat received from %d' % hb_msg.domino_udid

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
    print 'Registration Request received for UDID %d from IP: %s port: %d ' % (reg_msg.domino_udid_desired, reg_msg.ipaddr, reg_msg.tcpport)

   
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

    # Store the Domino Client info
    # TBD: check the sequence number to ensure the most recent record is saved
    self.dominoServer.registration_record[reg_r.domino_udid_assigned] = reg_msg 
    return reg_r


  #Subscription from Domino Client is received
  #Actions:
  #       - Save the templates  & labels
  #       - Respond Back with Subscription Response
  def d_subscribe(self, sub_msg):
    global SERVER_UDID, SERVER_SEQNO
    print 'Subscribe Request received from %d' % sub_msg.domino_udid

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
        if self.dominoServer.subscribed_labels.has_key(sub_msg.domino_udid):
          self.dominoServer.subscribed_labels[sub_msg.domino_udid].update(set(sub_msg.labels))
        else:
          self.dominoServer.subscribed_labels[sub_msg.domino_udid] = set(sub_msg.labels)
      elif sub_msg.label_op == OVERWRITE:
        self.dominoServer.subscribed_labels[sub_msg.domino_udid] = set(sub_msg.labels)
      elif sub_msg.label_op == DELETE:
        self.dominoServer.subscribed_labels[sub_msg.domino_udid].difference_update(set(sub_msg.labels))

    print 'Supported Template: %s' % self.dominoServer.subscribed_templateformats[sub_msg.domino_udid]
    print 'Supported Labels: %s' % self.dominoServer.subscribed_labels[sub_msg.domino_udid] 
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
    print 'Publish Request received from %d' % pub_msg.domino_udid
    print pub_msg.template

    # Save as file
    try:
      os.makedirs(TOSCADIR)
    except OSError as exception:
      if exception.errno == errno.EEXIST:
        print TOSCADIR, ' exists. Creating: ' , TOSCADIR+TOSCA_DEFAULT_FNAME
      else:
        print 'Error occurred in creating the directory. Err no: ', exception.errno

    #Risking a race condition if another process is attempting to write to same file
    f = open(TOSCADIR+TOSCA_DEFAULT_FNAME, 'w')  
    for item in pub_msg.template:
      print>>f, item
    f.close()

    # Load tosca object from file into memory
    tosca = ToscaTemplate( TOSCADIR+TOSCA_DEFAULT_FNAME )
    
    # Extract Labels
    node_labels = label.extract_labels( tosca )
    print '\nNode Labels: \n', node_labels

    # Map nodes in the template to resource domains
    site_map = label.map_nodes( self.dominoServer.subscribed_labels , node_labels )
    print '\nSite Maps: \n' , site_map

    # Select a site for each VNF
    node_site = label.select_site( site_map ) 
    print '\nSelected Sites:\n' , node_site , '\n'

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
   #   self.push_template(pub_msg.template, DOMINO_CLIENT_IP, DOMINO_CLIENT_PORT)

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
     self.log = {}
     self.assignedUUIDs = list()
     self.subscribed_labels = dict()
     self.subscribed_templateformats = dict()
     self.registration_record = dict() 
     self.communicationHandler = CommunicationHandler(self)
     self.processor = Communication.Processor(self.communicationHandler)
     self.transport = TSocket.TServerSocket(port=9090)
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
       new_udid = random.getrandbits(64)
       while new_udid in self.assignedUUIDs:
         new_udid = random.getrandbits(64)
 
       self.assignedUUIDs.append(new_udid)
       return new_udid
     else:
       self.assignedUUIDs.append(udid_desired)
       return udid_desired
   

def main(argv):
  server = DominoServer()
  print 'Starting the server...'
  server.start_communicationService()
  print 'done.'

if __name__ == "__main__":
   main(sys.argv[1:])
