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
    subscribe -l/--label <policytype>:properties:key:value
    
Example:
First checkout the tosca file "./tosca-templates/tosca_helloworld_nfv.yaml" and see how policy types and rules are defined. Then, from any Domino Client, use subscribe command as:

    subscribe --label tosca.policies.Placement.Geolocation:properties:region:us-west-1
 
###publish default template file under tosca-templates
    publish --tosca-file <path_to_toscafile>

Example:
Run the following command from any Domino Client:

    publish --tosca-file ./tosca-templates/tosca_helloworld_nfv.yaml

Now, inspect the files generated under ./toscafiles, where the original file as well as parts sent to each Domino Client are shown (each part identified by UDID assigned to that client)

##NOTES
  If accidentally you start DominoClient before DominoServer, don't panic. First start the DominoServer and then input the command on the DominoClient side:

    register
