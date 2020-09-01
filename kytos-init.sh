#!/bin/bash

set -x

service syslog-ng start
service openvswitch-switch start

for napp in storehouse of_core flow_manager topology of_lldp pathfinder mef_eline maintenance; do git clone https://github.com/kytos/$napp;  cd $napp; python3.6 setup.py develop || true; cd ..; done

apt-get update && apt-get install -y python-pytest python-requests python-mock python-pytest-timeout

python -m pytest --timeout=60 tests/

#only runs specific test
#python -m pytest --timeout=60 tests/test_e2e_10_mef_eline.py::TestE2EMefEline::test_on_primary_path_fail_should_migrate_to_backup

# leave tail running unless it is from Gitlab-CI
[ -z "$CI_PROJECT_ID" ] && tail -f /dev/null
