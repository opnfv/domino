# Domino

##Quick Start on the same machine:

Tested on Ubuntu 14.04 and OS X El Capitan

###Prerequisite:
    git clone https://gerrit.opnfv.org/gerrit/domino
    sudo apt-get install python-pip
    sudo pip install tosca-parser
    sudo pip install heat-translator

###Testing:    
Proceed to the domino folder and run a smoke test that checks APIs
 
    cd domino    
    ./tests/run.sh

###Common Errors
If "internal error" message is received, a python library is missing

Clean the server side database:

    rm -r dominoserver.db

Make sure that all the existing domino server and client processes are killed.
    kill $(pgrep -f "DominoServer.py")
    kill $(pgrep -f "DominoClient.py") 

###Start Domino Server:
    ./DominoServer.py --log=DEBUG

###Start the first Domino Client:
    ./DominoClient.py -p 9091 --cliport 9100 --log=DEBUG

Note: if --log option is ommitted, the default logging level is Warning messages

###Start the second Domino Client:
    ./DominoClient.py -p 9092 --cliport 9200 --log=DEBUG

##CLI at the Domino Client:

###Send heartbeat
    python domino-cli.py <cliport> heartbeat

###Subscribe for policy labels
    python domino-cli.py <cliport> subscribe -l/--label <policytype>:properties:key:value
    
Example:
First checkout the tosca file "./tosca-templates/tosca_helloworld_nfv.yaml" and see how policy types and rules are defined. Then, for the first Domino Client, use subscribe command as:

    python domino-cli.py 9100 subscribe --label tosca.policies.Placement.Geolocation:properties:region:us-west-1
 
###Publish default template file under tosca-templates
    python domino-cli.py <cliport> publish --tosca-file <path_to_toscafile>

Example:
Run the following command for the second Domino Client:

    python domino-cli.py 9200 publish --tosca-file ./tosca-templates/tosca_helloworld_nfv.yaml

Now, inspect the files generated under ./toscafiles, where the original file as well as parts sent to each Domino Client are shown (each part identified by UDID assigned to that client)

###Query published tosca-templates for each client
    python domino-cli.py <cliport> list-tuids

Example:
Run the following command for the second Domino Client:
    python domino-cli.py 9200 list-tuids

###Change the published template for a specific Template Unique ID (TUID)
    python domino-cli.py <cliport> publish -t ./tosca-templates/tosca_helloworld_nfv.yaml -k <TUID>

Example:
Run the following command for the second Domino Client:
    TUID=$(python domino-cli.py 9200 list-tuids | cut -c3-34)
    python domino-cli.py 9200 publish -t ./tosca-templates/tosca_helloworld_nfv.yaml -k "$TUID"

##NOTES
  If accidentally you start DominoClient before DominoServer, don't panic. First start the DominoServer and then input the command on the DominoClient side:

    register
