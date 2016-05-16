# Domino

##Quick Start on the same machine:

Tested on Ubuntu 14.04 and OS X El Capitan

###Prerequisite:
    sudo pip install tosca-parser

###Start Domino Server:
    ./DominoServer.py

###Start the first Domino Client:
    ./DominoClient.py -p 9091

###Start the second Domino Client:
    ./DominoClient.py -p 9092

##CLI at the Domino Client:

###send heartbeat
    heartbeat

###subscribe for policy labels
    subscribe -l/--labels <policytype>:properties:key:value

###publish default template file under tosca-templates
    publish --tosca-file <path_to_toscafile>
