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

import sys, glob, getopt
import getopt

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

def main(argv, cli_port):
  #cli_port = DOMINO_CLI_PORT

  try:
    # Make socket
    # NOTE that domino-cli.py and DominoClient.py are assumed to be run in the same machine
    transport = TSocket.TSocket('localhost', int(cli_port))
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

  except Thrift.TException, tx:
    print '%s' % (tx.message)

if __name__ == "__main__":
   if len(sys.argv) >= 2:
     main(sys.argv[2:], sys.argv[1])
   else:
     print 'domino-cli.py <cliport> ...'
     sys.exit(2)
