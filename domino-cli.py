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

import sys, glob, getopt

sys.path.insert(0, glob.glob('./lib')[0])

from dominoCLI import DominoClientCLI
from dominoCLI.ttypes import *
from dominoCLI.constants import *

from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

#Load configuration parameters
from domino_conf import *

def main(argv):
#  try:
#    if argv[0] == 'heartbeat':
#      print 'Heartbeat input'
#  except IndexError as ex:
#    print 'Insufficient number of arguments entered'
#  except:
#    print('Error: %s', sys.exc_info()[0])

  try:
    # Make socket
    transport = TSocket.TSocket('localhost', DOMINO_CLI_PORT)
    # Buffering is critical. Raw sockets are very slow
    transport = TTransport.TBufferedTransport(transport)
    # Wrap in a protocol
    protocol = TBinaryProtocol.TBinaryProtocol(transport)

    # Create a client to use the protocol encoder
    client = DominoClientCLI.Client(protocol)

    # Connect!
    transport.open()

    CLImsg = CLIMessage()
    CLImsg.CLI_input = argv
    CLIrespmsg = client.d_CLI(CLImsg)
    print CLIrespmsg.CLI_response

  except Thrift.TException, tx:
    print '%s' % (tx.message)

if __name__ == "__main__":
   main(sys.argv[1:])
