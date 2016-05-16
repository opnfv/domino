#!/usr/bin/env python

#
# Licence statement goes here
#

import sys, glob, threading
import getopt

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

from util import *

CLIENT_UDID = 1
CLIENT_SEQNO = 0

DOMINO_SERVER_IP = 'localhost'
DOMINO_SERVER_PORT = 9090

UDID_DESIRED = 12467
LIST_SUPPORTED_TEMPLATES = ['tosca-nfv-v1.0']
#DEFAULT_TOSCA_PUBFILE = './tosca-templates/tosca_simpleVNF.yaml'
DEFAULT_TOSCA_PUBFILE = './tosca-templates/tosca_helloworld_nfv.yaml'

class CommunicationHandler:
  def __init__(self):
    self.log = {}

  def __init__(self, dominoclient):
    global DOMINO_SERVER_IP, DOMINO_SERVER_PORT
    self.log = {}
    self.dominoClient = dominoclient
    try:
      # Make socket
      transport = TSocket.TSocket(DOMINO_SERVER_IP, DOMINO_SERVER_PORT)
      # Add buffering to compensate for slow raw sockets
      self.transport = TTransport.TBufferedTransport(transport)
      # Wrap in a protocol
      self.protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
      # Create a client to use the protocol encoder
      self.sender = Communication.Client(self.protocol)
    except Thrift.TException, tx: 
      print '%s' % (tx.message)

  # Template Push from Domino Server is received
  # Actions:
  #       - Depending on Controller Domain, call API
  #       - Respond Back with Push Response
  def d_push(self, push_msg):
    print 'Received Template File'
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
 
def read_templatefile(temp_filename): 
  f = open(temp_filename, 'r')
  lines = f.read().splitlines()

  return lines

class DominoClientCLIService(threading.Thread):
  def __init__(self, dominoclient, communicationhandler):
    threading.Thread.__init__(self)
    self.dominoclient = dominoclient
    self.communicationhandler = communicationhandler

  def run(self):
    global DEFAULT_TOSCA_PUBFILE
    while True:
       sys.stdout.write('>>')
       input_string = raw_input()
       args = input_string.split()
       if len(args) == 0:
         continue

       labels = []       
       templateTypes = []

       #process input arguments
       try:
         sys.stdout.write('>>')
         if args[0] == 'heartbeat':
           print '\nSending heatbeat'
           hbm = HeartBeatMessage()
           hbm.domino_udid = self.dominoclient.UDID
           hbm.seq_no = self.dominoclient.seqno
           hbm_r = self.communicationhandler.sender.d_heartbeat(hbm)
           print 'heart beat received from: %d ,sequence number: %d' % (hbm_r.domino_udid, hbm_r.seq_no)
           self.dominoclient.seqno = self.dominoclient.seqno + 1
         
         elif args[0] == 'publish':
           opts, args = getopt.getopt(args[1:],"t:",["tosca-file="])
           if len(opts) == 0:
             print '\nUsage: publish -t <toscafile>'
             continue

           #toscafile = DEFAULT_TOSCA_PUBFILE
           for opt, arg in opts:
             if opt in ('-t', '--tosca-file'):
               toscafile = arg
           
           pub_msg = PublishMessage()
           pub_msg.domino_udid = self.dominoclient.UDID
           pub_msg.seq_no = self.dominoclient.seqno
           pub_msg.template_type = 'tosca-nfv-v1.0'
           try:
             pub_msg.template = read_templatefile(toscafile)
           except IOError as e:
             print "I/O error({0}): {1}".format(e.errno, e.strerror)
             continue
           print '\nPublishing the template file: ' + toscafile
           pub_msg_r = self.communicationhandler.sender.d_publish(pub_msg)
           print 'Publish Response is received from: %d ,sequence number: %d' % (pub_msg_r.domino_udid, pub_msg_r.seq_no)
           self.dominoclient.seqno = self.dominoclient.seqno + 1
       
         elif args[0] == 'subscribe':         
           opts, args = getopt.getopt(args[1:],"l:t:",["labels=","ttype="])
           for opt, arg in opts:
              if opt in ('-l', '--labels'):
                 labels = labels + arg.split(',')
              elif opt in ('-t', '--ttype'):
                 templateTypes = templateTypes + arg.split(',')
 
       except getopt.GetoptError:
         print 'Command is misentered or not supported!'


       #check if labels or supported templates are nonempty
       if labels != [] or templateTypes != []:
         #send subscription message
         sub_msg = SubscribeMessage()
         sub_msg.domino_udid = self.dominoclient.UDID
         sub_msg.seq_no = self.dominoclient.seqno
         sub_msg.template_op = APPEND
         sub_msg.supported_template_types = templateTypes
         sub_msg.label_op = APPEND
         sub_msg.labels = labels
         print 'subscribing labels %s and templates %s' % (labels,templateTypes)
         sub_msg_r = self.communicationhandler.sender.d_subscribe(sub_msg) 
         print 'Subscribe Response is received from: %d ,sequence number: %d' % (sub_msg_r.domino_udid,sub_msg_r.seq_no)
         self.dominoclient.seqno = self.dominoclient.seqno + 1

class DominoClient:
  def __init__(self):
    self.log = {}
    self.communicationHandler = CommunicationHandler(self)
    self.processor = None
    self.transport = None
    self.tfactory = None
    self.pfactory = None
    self.communicationServer = None

    self.CLIservice = DominoClientCLIService(self, self.communicationHandler)

    self.serviceport = 9091
    self.dominoserver_IP = 'localhost'

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
    except Thrift.TException, tx:
      print '%s' % (tx.message)
    
    if self.state == 'UNREGISTERED':
      #prepare registration message
      reg_msg = RegisterMessage()
      reg_msg.domino_udid_desired = UDID_DESIRED
      reg_msg.seq_no = self.seqno
      reg_msg.ipaddr = netutil.get_ip()
      reg_msg.tcpport = self.serviceport
      reg_msg.supported_templates = LIST_SUPPORTED_TEMPLATES

      reg_msg_r = self.sender().d_register(reg_msg)
      print 'Registration Response:\n'
      print 'Response Code: %d'  % (reg_msg_r.responseCode)
      print 'Response Comments:'
      if reg_msg_r.comments:
        print reg_msg_r.comments

      if reg_msg_r.responseCode == SUCCESS:
        self.state = 'REGISTERED'
        self.UDID = reg_msg_r.domino_udid_assigned
      else:
        #Handle registration failure here (possibly based on reponse comments)   
        pass

      self.seqno = self.seqno + 1

  def stop(self):
    try:
      self.communicationHandler.closeconnection()
    except Thrift.TException, tx:
      print '%s' % (tx.message)
    
  def sender(self):
    return self.communicationHandler.sender

  def startCLI(self):
    print 'CLI Service is starting'
    self.CLIservice.start()
    #to wait until CLI service is finished
    #self.CLIservice.join()

  def set_serviceport(self, port):
    self.serviceport = port
    print 'port: '
    print self.serviceport

  def set_dominoserver_ipaddr(self, ipaddr):
    self.dominoserver_IP = ipaddr
    print 'ip addr: '
    print self.dominoserver_IP

def main(argv):
  client = DominoClient()

  #process input arguments
  try:
      opts, args = getopt.getopt(argv,"hc:p:i:",["conf=","port=","ipaddr="])
  except getopt.GetoptError:
      print 'DominoClient.py -c/--conf <configfile> -p/--port <socketport> -i/--ipaddr <IPaddr>'
      sys.exit(2)
  for opt, arg in opts:
      if opt == '-h':
         print 'DominoClient.py -c/--conf <configfile> -p/--port <socketport> -i/--ipaddr <IPaddr>'
         sys.exit()
      elif opt in ("-c", "--conf"):
         configfile = arg
      elif opt in ("-p", "--port"):
         client.set_serviceport(int(arg))
      elif opt in ("-i", "--ipaddr"):
         client.set_dominoserver_ipaddr(arg)

  #The client is starting
  print 'Starting the client...'
  client.start()
  client.startCLI()
  client.start_communicationService()

if __name__ == "__main__":
   main(sys.argv[1:])

