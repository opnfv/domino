#!/bin/bash -ex

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

USERNAME=ubuntu
SSH_KEY_PATH=/home/opnfv/.ssh/id_rsa
DOMINO_CODE_PATH=/home/opnfv/repos/domino
CONTROLLER_NODE_1=192.168.2.165
CONTROLLER_NODE_2=192.168.2.180
CONTROLLER_NODE_3=192.168.2.181

CLIENT1_PORT=9091
CLIENT2_PORT=9092
CLIENT1_CLIPORT=9100
CLIENT2_CLIPORT=9200
LOGLEVEL=DEBUG

toscafile_test1=./tosca-templates/tosca_helloworld_nfv.yaml
test1_reffile1=./tests/refdata/test1_client1.ref
test1_reffile2=./tests/refdata/test1_client2.ref
client1_log=./tests/logdata/client1.log
client2_log=./tests/logdata/client2.log
server_log=./tests/logdata/server.log

install_dependency() {
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" 'sudo pip install tosca-parser'
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" 'sudo pip install heat-translator'
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_2" 'sudo pip install tosca-parser'
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_2" 'sudo pip install heat-translator'
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_3" 'sudo pip install tosca-parser'
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_3" 'sudo pip install heat-translator'
}

remove_codes(){
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" 'rm -rf domino'
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_2" 'rm -rf domino'
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_3" 'rm -rf domino'
}

deploy_codes(){
  scp -i "$SSH_KEY_PATH" -r "$DOMINO_CODE_PATH" "$USERNAME"@"$CONTROLLER_NODE_1":.
  scp -i "$SSH_KEY_PATH" -r "$DOMINO_CODE_PATH" "$USERNAME"@"$CONTROLLER_NODE_2":.
  scp -i "$SSH_KEY_PATH" -r "$DOMINO_CODE_PATH" "$USERNAME"@"$CONTROLLER_NODE_3":.
}

start_server() {
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" 'pgrep -f "python DominoServer.py"' && return 0
  ssh -f -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" "sh -c 'cd ./domino; nohup python DominoServer.py --log "$LOGLEVEL" > "$server_log" > /dev/null 2>&1 &'"
}

start_client1() {
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_2" 'pgrep -f "python DominoClient.py"' && return 0
  ssh -f -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_2" "sh -c 'cd ./domino; nohup python DominoClient.py -p $CLIENT1_PORT --cliport $CLIENT1_CLIPORT --ipaddr $CONTROLLER_NODE_1 --log "$LOGLEVEL" > "$client1_log" > /dev/null 2>&1 &'"
}

start_client2() {
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_3" 'pgrep -f "python DominoClient.py"' && return 0
  ssh -f -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_3" "sh -c 'cd ./domino; nohup python DominoClient.py -p $CLIENT2_PORT --cliport $CLIENT2_CLIPORT --ipaddr $CONTROLLER_NODE_1 --log "$LOGLEVEL" > "$client2_log" > /dev/null 2>&1 &'"
}

stop_server() {
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" 'pgrep -f "python DominoServer.py"' || return 0
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" 'kill $(pgrep -f "python DominoServer.py")'
}

stop_client1() {
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_2" 'pgrep -f "python DominoClient.py"' || return 0
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_2" 'kill $(pgrep -f "python DominoClient.py")'
}

stop_client2() {
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_3" 'pgrep -f "python DominoClient.py"' || return 0
  ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_3" 'kill $(pgrep -f "python DominoClient.py")'
}

cleanup() {
  set +e
  echo "cleanup..."
  
  echo "Stopping Domino Clients..."
  stop_client1
  stop_client2
 
  echo "Stopping Domino Server..."
  stop_server
  sleep 1
}

prepare_testenv() {
  install_dependency
  remove_codes
  deploy_codes
}

launch_domino() {
  echo "Launching Domino Server..."
  start_server
  sleep 1
  echo "Launching Domino Client 1..."
  start_client1
  sleep 1
  echo "Launching Domino Client 2..."
  start_client2
  sleep 1
}

echo "domino/tests/run_multinode.sh has been executed."

trap cleanup EXIT

cleanup
prepare_testenv
launch_domino


echo "Test Heartbeat"
ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" \ 
	'python domino-cli.py $CLIENT1_CLIPORT heartbeat'
sleep 1

echo "Test Subscribe API"
ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" \
	'python domino-cli.py $CLIENT1_CLIPORT subscribe -t hot \
	-l tosca.policies.Placement:properties:region:nova-1'  
sleep 1
ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" \
	'python domino-cli.py $CLIENT1_CLIPORT subscribe -t dummy1,dummy2 --top OVERWRITE'
sleep 1
ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" \
	'python domino-cli.py $CLIENT1_CLIPORT subscribe -t dummy1,dummy2 --top DELETE'
sleep 1
ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" \
	'python domino-cli.py $CLIENT1_CLIPORT subscribe \
         -l tosca.policies.Placement:properties:region:nova-2'
sleep 1
ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" \
	'python domino-cli.py $CLIENT1_CLIPORT subscribe \
	 -l tosca.policies.Placement:properties:region:nova-3 \
	 --lop OVERWRITE'
sleep 1
ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" \
	'python domino-cli.py $CLIENT1_CLIPORT subscribe \
         -l tosca.policies.Placement:properties:region:nova-3 \
	 --lop DELETE'
sleep 1

echo "Test Publish API"
ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" \
	'python domino-cli.py $CLIENT1_CLIPORT publish -t "$toscafile_test1"' 

sleep 1
ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_1" \
	'python domino-cli.py $CLIENT1_CLIPORT subscribe \
         -l tosca.policies.Placement.Geolocation:properties:region:us-west-1'
sleep 1
ssh -i "$SSH_KEY_PATH" "$USERNAME"@"$CONTROLLER_NODE_2" \
	'python domino-cli.py $CLIENT2_CLIPORT publish -t "$toscafile_test1"'

echo "done"

