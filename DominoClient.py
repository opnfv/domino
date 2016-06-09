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


import sys, glob, threading
import getopt, socket
import logging

#sys.path.append('gen-py')
#sys.path.insert(0, glob.glob('./lib/py/build/lib.*')[0])
sys.path.insert(0, glob.glob('./lib')[0])

from dominoRPC import Communication
from dominoRPC.ttypes import *
from dominoRPC.constants import *

from dominoCLI import DominoClientCLI
from dominoCLI.ttypes import *
from dominoCLI.constants import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

from util import *

#Load configuration parameters
from domino_conf import *

class CommunicationHandler:
  def __init__(self):
    self.log = {}

  def __init__(self, dominoclient):
    self.log = {}
    self.dominoClient = dominoclient
    try:
      # Make socket
      transport = TSocket.TSocket(DOMINO_SERVER_IP, DOMINO_SERVER_PORT)
      transport.setTimeout(THRIFT_RPC_TIMEOUT_MS)
      # Add buffering to compensate for slow raw sockets
      self.transport = TTransport.TBufferedTransport(transport)
      # Wrap in a protocol
      self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
      # Create a client to use the protocol encoder
      self.sender = Communication.Client(self.protocol)
    except Thrift.TException, tx: 
      logging.error('%s' , tx.message)

  # Template Push from Domino Server is received
  # Actions:
  #       - Depending on Controller Domain, call API
  #       - Respond Back with Push Response
  def d_push(self, push_msg):
    logging.info('%d Received Template File', self.dominoClient.UDID)
    # Retrieve the template file

    ## End of retrieval
 
    # Any inspection code goes here

    ## End of inspection

    # Call NB API
    # If heat client, call heat command
    
    # If ONOS client, run as shell script


    ## End of NB API call

    # Marshall the response message for the Domino Server Fill
    push_r = PushResponseMessage()
    # Fill response message fields
    push_r.domino_udid = self.dominoClient.UDID    
    push_r.seq_no = self.dominoClient.seqno
    push_r.responseCode = SUCCESS    
    ## End of filling

    self.dominoClient.seqno = self.dominoClient.seqno + 1

    return push_r

  
  def openconnection(self):
    self.transport.open()

  def closeconnection():
    self.transport.close()

class CLIHandler:
  def __init__(self):
    self.log = {}

  def __init__(self, dominoclient, CLIservice):
    self.log = {}
    self.dominoClient = dominoclient
    self.CLIservice = CLIservice

  def d_CLI(self, msg):
    logging.info('Received CLI %s', msg.CLI_input)

    self.CLIservice.process_input(msg.CLI_input)
    
    CLIrespmsg = CLIResponse()
    CLIrespmsg.CLI_response = "Testing..."
    return CLIrespmsg
 

class DominoClientCLIService(threading.Thread):
  def __init__(self, dominoclient, communicationhandler, interactive):
    threading.Thread.__init__(self)
    self.dominoclient = dominoclient
    self.communicationhandler = communicationhandler
    self.interactive = interactive

  def process_input(self, args):
    try:
      if args[0] == 'heartbeat':
        self.dominoclient.heartbeat()

      elif args[0] == 'publish':
        opts, args = getopt.getopt(args[1:],"t:",["tosca-file="])
        if len(opts) == 0:
	  print '\nUsage: publish -t <toscafile>'
	  return

        for opt, arg in opts:
	  if opt in ('-t', '--tosca-file'):
	    toscafile = arg
       
        self.dominoclient.publish(toscafile)

      elif args[0] == 'subscribe':
        labels = []    
        templateTypes = []
        labelop = APPEND
        templateop = APPEND
        opts, args = getopt.getopt(args[1:],"l:t:",["labels=","ttype=","lop=","top="])
        for opt, arg in opts:
	  if opt in ('-l', '--labels'):
	    labels = labels + arg.split(',')
	  elif opt in ('-t', '--ttype'):
	    templateTypes = templateTypes + arg.split(',')
          elif opt in ('--lop'):
            try:
              labelop = str2enum[arg.upper()]
            except KeyError as ex:
              print '\nInvalid label option, pick one of: APPEND, OVERWRITE, DELETE'
              return 
          elif opt in ('--top'):
            try:
              templateop = str2enum[arg.upper()]
            except KeyError as ex:
              print '\nInvalid label option, pick one of: APPEND, OVERWRITE, DELETE'
              return
        
        #check if labels or supported templates are nonempty
        if labels != [] or templateTypes != []:
          self.dominoclient.subscribe(labels, templateTypes, labelop, templateop)

      elif args[0] == 'register':
        self.dominoclient.start()

    except getopt.GetoptError:
      print 'Command is misentered or not supported!'


  def run(self):
    global DEFAULT_TOSCA_PUBFILE
    if self.interactive == "TRUE":
      flag = True
    else:
      flag = False

    if flag: #interactive CLI, loop in while until killed
      while True:
	 sys.stdout.write('>>')
	 input_string = raw_input()
	 args = input_string.split()
	 if len(args) == 0:
	   continue

         sys.stdout.write('>>')
	 #process input arguments
         self.process_input(args)
    else: #domino cli-client is used, listen for the CLI rpc calls
      cliHandler = CLIHandler(self.dominoclient, self)
      processor = DominoClientCLI.Processor(cliHandler)
      transport = TSocket.TServerSocket(port=self.dominoclient.CLIport)
      tfactory = TTransport.TBufferedTransportFactory()
      pfactory = TBinaryProtocol.TBinaryProtocolFactory()
      #Use TThreadedServer or TThreadPoolServer for a multithreaded server
      CLIServer = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
      logging.debug('RPC service for CLI is starting...')
      CLIServer.serve()       

class DominoClient:
  def __init__(self):
    self.communicationHandler = CommunicationHandler(self)
    self.processor = None
    self.transport = None
    self.tfactory = None
    self.pfactory = None
    self.communicationServer = None

    self.CLIservice = None

    self.serviceport = 9091
    self.dominoserver_IP = 'localhost'

    self.CLIport = DOMINO_CLI_PORT 

    #Start from UNREGISTERED STATE
    #TO BE DONE: initialize from a saved state
    self.state = 'UNREGISTERED'
    self.seqno = 0
    self.UDID = 1

  def start_communicationService(self):
    self.processor = Communication.Processor(self.communicationHandler)
    self.transport = TSocket.TServerSocket(port=int(self.serviceport))
    self.tfactory = TTransport.TBufferedTransportFactory()
    self.pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    #Use TThreadedServer or TThreadPoolServer for a multithreaded server
    #self.communicationServer = TServer.TThreadedServer(self.processor, self.transport, self.tfactory, self.pfactory)
    self.communicationServer = TServer.TThreadPoolServer(self.processor, self.transport, self.tfactory, self.pfactory)

    self.communicationServer.serve()
 
  def start(self):
    try:
      self.communicationHandler.openconnection()
      self.register()
    except Thrift.TException, tx:
      print '%s' % (tx.message)
   
  def register(self):  
    if self.state == 'UNREGISTERED':
      logging.info('%d Sending Registration', self.UDID)
      #prepare registration message
      reg_msg = RegisterMessage()
      reg_msg.domino_udid_desired = UDID_DESIRED
      reg_msg.seq_no = self.seqno
      reg_msg.ipaddr = netutil.get_ip()
      reg_msg.tcpport = self.serviceport
      reg_msg.supported_templates = LIST_SUPPORTED_TEMPLATES

      try:
        reg_msg_r = self.sender().d_register(reg_msg)
        logging.info('Registration Response: Response Code: %d'  , reg_msg_r.responseCode)
        if reg_msg_r.comments:
          logging.debug('Response Comments: %s' ,  reg_msg_r.comments)

        if reg_msg_r.responseCode == SUCCESS:
          self.state = 'REGISTERED'
          self.UDID = reg_msg_r.domino_udid_assigned
        else:
          #Handle registration failure here (possibly based on reponse comments)
          pass
      except (Thrift.TException, TSocket.TTransportException) as tx:
        logging.error('%s' , tx.message)
      except (socket.timeout) as tx:
        self.dominoclient.handle_RPC_timeout(pub_msg)
      except (socket.error) as tx:
        logging.error('%s' , tx.message)
      self.seqno = self.seqno + 1

  def heartbeat(self):
    if self.state == 'UNREGISTERED':
      self.start()
          
    logging.info('%d Sending heartbeat', self.UDID)
    hbm = HeartBeatMessage()         
    hbm.domino_udid = self.UDID        
    hbm.seq_no = self.seqno         

    try:
      hbm_r = self.sender().d_heartbeat(hbm)
      logging.info('heart beat received from: %d ,sequence number: %d' , hbm_r.domino_udid, hbm_r.seq_no)
    except (Thrift.TException, TSocket.TTransportException) as tx:
      logging.error('%s' , tx.message)
    except (socket.timeout) as tx:
      self.handle_RPC_timeout(hbm)
    except:
      logging.error('Unexpected error: %s', sys.exc_info()[0])
    
    self.seqno = self.seqno + 1    

  def publish(self, toscafile):
    if self.state == 'UNREGISTERED':
      self.start()

    logging.info('Publishing the template file: ' + toscafile)
    pub_msg = PublishMessage()
    pub_msg.domino_udid = self.UDID
    pub_msg.seq_no = self.seqno
    pub_msg.template_type = 'tosca-nfv-v1.0'

    try:
      pub_msg.template = miscutil.read_templatefile(toscafile)
    except IOError as e:
      logging.error('I/O error(%d): %s' , e.errno, e.strerror)
      return
    try:
      pub_msg_r = self.sender().d_publish(pub_msg)
      logging.info('Publish Response is received from: %d ,sequence number: %d Op. Status: %d', pub_msg_r.domino_udid, pub_msg_r.seq_no, pub_msg_r.responseCode)
    except (Thrift.TException, TSocket.TTransportException) as tx:
      print '%s' % (tx.message)
    except (socket.timeout) as tx:
      self.handle_RPC_timeout(pub_msg)

    self.seqno = self.seqno + 1

  def subscribe(self, labels, templateTypes, label_op, template_op):
     if self.state == 'UNREGISTERED':
       self.start()

     logging.info('subscribing labels %s and templates %s', labels, templateTypes)
     #send subscription message
     sub_msg = SubscribeMessage()
     sub_msg.domino_udid = self.UDID
     sub_msg.seq_no = self.seqno
     sub_msg.template_op = template_op
     sub_msg.supported_template_types = templateTypes
     sub_msg.label_op = label_op
     sub_msg.labels = labels
     try:
       sub_msg_r = self.sender().d_subscribe(sub_msg)
       logging.info('Subscribe Response is received from: %d ,sequence number: %d', sub_msg_r.domino_udid,sub_msg_r.seq_no)
     except (Thrift.TException, TSocket.TTransportException) as tx: 
       logging.error('%s' , tx.message)
     except (socket.timeout) as tx: 
       self.handle_RPC_timeout(sub_msg)

     self.seqno = self.seqno + 1 

  def stop(self):
    try:
      self.communicationHandler.closeconnection()
    except Thrift.TException, tx:
      logging.error('%s' , tx.message)
    
  def sender(self):
    return self.communicationHandler.sender

  def startCLI(self, interactive):
    self.CLIservice = DominoClientCLIService(self, self.communicationHandler, interactive)
    logging.info('CLI Service is starting')
    self.CLIservice.start()
    #to wait until CLI service is finished
    #self.CLIservice.join()

  def set_serviceport(self, port):
    self.serviceport = port

  def set_CLIport(self, cliport):
    self.CLIport = cliport

  def set_dominoserver_ipaddr(self, ipaddr):
    self.dominoserver_IP = ipaddr

  def handle_RPC_timeout(self, RPCmessage):
    # TBD: handle each RPC timeout separately
    if RPCmessage.messageType == HEART_BEAT:
      logging.debug('RPC Timeout for message type: HEART_BEAT') 
    elif RPCmessage.messageType == PUBLISH:
      logging.debug('RPC Timeout for message type: PUBLISH')
    elif RPCmessage.messageType == SUBSCRIBE:
      logging.debug('RPC Timeout for message type: SUBSCRIBE')
    elif RPCmessage.messageType == REGISTER:
      logging.debug('RPC Timeout for message type: REGISTER')
    elif RPCmessage.messageType == QUERY:
      logging.debug('RPC Timeout for message type: QUERY') 

def main(argv):
  client = DominoClient()
  loglevel = LOGLEVEL
  interactive = INTERACTIVE
  #process input arguments
  try:
      opts, args = getopt.getopt(argv,"hc:p:i:l:",["conf=","port=","ipaddr=","log=","iac=","cliport="])
  except getopt.GetoptError:
      print 'DominoClient.py -c/--conf <configfile> -p/--port <socketport> -i/--ipaddr <IPaddr> -l/--log <loglevel> --iac=true/false'
      sys.exit(2)
  for opt, arg in opts:
      if opt == '-h':
         print 'DominoClient.py -c/--conf <configfile> -p/--port <socketport> -i/--ipaddr <IPaddr> -l/--log <loglevel> --iac=true/false'
         sys.exit()
      elif opt in ("-c", "--conf"):
         configfile = arg
      elif opt in ("-p", "--port"):
         client.set_serviceport(int(arg))
      elif opt in ("-i", "--ipaddr"):
         client.set_dominoserver_ipaddr(arg)
      elif opt in ("-l", "--log"):
         loglevel = arg
      elif opt in ("--iac"):
         interactive = arg.upper()
      elif opt in ("--cliport"):
         client.set_CLIport(int(arg))

  #Set logging level
  numeric_level = getattr(logging, loglevel.upper(), None)
  try:
    if not isinstance(numeric_level, int):
      raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(filename=logfile,level=numeric_level, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
  except ValueError, ex:
    print ex.message
    exit()
 
  #The client is starting
  logging.debug('Domino Client Starting...')
  client.start()
  client.startCLI(interactive)
  client.start_communicationService()

if __name__ == "__main__":
   main(sys.argv[1:])

