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

CLIENT1_PORT=9091
CLIENT2_PORT=9092
CLIENT1_CLIPORT=9100
CLIENT2_CLIPORT=9200
LOGLEVEL=DEBUG

toscafile_test1=./tosca-templates/tosca_helloworld_nfv.yaml
test1_reffile=./tests/refdata/test1.ref
client1_log=./tests/logdata/client1.log
server_log=./tests/logdata/server.log

start_server() {
  pgrep -f "python DominoServer.py" && return 0  
  python DominoServer.py --log "$LOGLEVEL" > "$server_log" 2>&1 &
}

stop_server() {
  pgrep -f "python DominoServer.py" || return 0  
  kill $(pgrep -f "python DominoServer.py")
  #cat server.log
}

start_client1() {
  pgrep -f "python DominoClient.py" && return 0
  python DominoClient.py -p $CLIENT1_PORT --cliport $CLIENT1_CLIPORT \
	--log "$LOGLEVEL" > "$client1_log" 2>&1 &
}

stop_client1() {
  pgrep -f "python DominoClient.py" || return 0
  kill $(pgrep -f "python DominoClient.py")
  #cat client1.log
}

clean_directories() {
  if [ -f dominoserver.db ]; then
    rm dominoserver.db
  fi

  if [ -d toscafiles ]; then
    rm -rf toscafiles
  fi
}

cleanup() {
  set +e
  echo "cleanup..."
  
  echo "Stopping Domino Client 1..."
  stop_client1

  echo "Stopping Domino Server..."
  stop_server

  if [ -f file1 ]; then
    rm file1
  fi
}

echo "domino/tests/run.sh has been executed."

trap cleanup EXIT

echo "Cleaning residue files and folders from previous runs..."
clean_directories

echo "Launching Domino Server..."
start_server
sleep 1

echo "Launching Domino Client 1..."
start_client1
sleep 1

echo "Test Heartbeat"
python domino-cli.py $CLIENT1_CLIPORT heartbeat
sleep 1

echo "Test Subscribe API"
python domino-cli.py $CLIENT1_CLIPORT subscribe -t hot \
	-l tosca.policies.Placement:properties:region:nova-1  
sleep 1
python domino-cli.py $CLIENT1_CLIPORT subscribe -t dummy1,dummy2 --top OVERWRITE
sleep 1
python domino-cli.py $CLIENT1_CLIPORT subscribe -t dummy1,dummy2 --top DELETE
sleep 1
python domino-cli.py $CLIENT1_CLIPORT subscribe \
        -l tosca.policies.Placement:properties:region:nova-2 \
sleep 1
python domino-cli.py $CLIENT1_CLIPORT subscribe \
	-l tosca.policies.Placement:properties:region:nova-3 \
	--lop OVERWRITE
sleep 1
python domino-cli.py $CLIENT1_CLIPORT subscribe \
        -l tosca.policies.Placement:properties:region:nova-3 \
	--lop DELETE
sleep 1

echo "Test Publish API"
python domino-cli.py $CLIENT1_CLIPORT publish -t "$toscafile_test1" 

sleep 5

#echo "Stopping Domino Client 1..."
#stop_client1

#echo "Stopping Domino Server..."
#stop_server

cut -d " " -f 4- "$client1_log" > file1
#will use the form below to declare success or failure
diff -q file1 "$test1_reffile" 1>/dev/null
if [[ $? == "0" ]]
then
  echo "SUCCESS"
else
  echo "FAILURE"
fi


echo "done"
