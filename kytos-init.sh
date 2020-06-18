#!/bin/bash

set -x

service syslog-ng start
service openvswitch-switch start
for napp in storehouse of_core flow_manager topology of_lldp pathfinder mef_eline; do git clone https://github.com/kytos/$napp;  cd $napp; python3.6 setup.py develop || true; cd ..; done
kytosd &
apt-get update
apt-get install -y python-pytest python-requests python-mock
python -m pytest tests/
#tail -f /dev/null
