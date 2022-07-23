#!/bin/bash

set -xe

# XXX: disable sdntrace and sdntrace_cp by default (along with their deps) while we are working on issue #110
for napp in amlight/coloring amlight/sdntrace amlight/scheduler amlight/flow_stats amlight/sdntrace_cp; do
   FILE=/var/lib/kytos/napps/$napp
   test -h $FILE && unlink $FILE
done

# the settings below are intended to decrease the tests execution time (in fact, the time.sleep() calls
# depend on the values below, otherwise many tests would fail)
sed -i 's/STATS_INTERVAL = 60/STATS_INTERVAL = 3/g' /var/lib/kytos/napps/kytos/of_core/settings.py
sed -i 's/LINK_UP_TIMER = 10/LINK_UP_TIMER = 1/g' /var/lib/kytos/napps/kytos/topology/settings.py
sed -i 's/DEPLOY_EVCS_INTERVAL = 60/DEPLOY_EVCS_INTERVAL = 5/g' /var/lib/kytos/napps/kytos/mef_eline/settings.py
sed -i 's/BOX_RESTORE_TIMER = 0.1/BOX_RESTORE_TIMER = 0.5/' /var/lib/kytos/napps/kytos/flow_manager/settings.py
sed -i 's/LLDP_LOOP_ACTIONS = \["log"\]/LLDP_LOOP_ACTIONS = \["disable","log"\]/' /var/lib/kytos/napps/kytos/of_lldp/settings.py
sed -i 's/LLDP_IGNORED_LOOPS = {"00:00:00:00:00:00:00:01": \[\[4, 5\]\]}/LLDP_IGNORED_LOOPS = {}/' /var/lib/kytos/napps/kytos/of_lldp/settings.py
sed -i 's/LLDP_IGNORED_LOOPS = {}/LLDP_IGNORED_LOOPS = {"00:00:00:00:00:00:00:01": \[\[4, 5\]\]}/' /var/lib/kytos/napps/kytos/of_lldp/settings.py
#sed -i 's/LLDP_IGNORED_LOOPS = {"00:00:00:00:00:00:00:01": \[\[4, 5\]\]}/LLDP_IGNORED_LOOPS = {}/' /var/lib/kytos/napps/kytos/of_lldp/settings.py
sed -n '10p' /var/lib/kytos/napps/kytos/of_lldp/settings.py
sed -n '11p' /var/lib/kytos/napps/kytos/of_lldp/settings.py

# increase logging to facilitate troubleshooting
kytosd --help >/dev/null 2>&1  ## create configs at /etc/kytos from templates
sed -i 's/WARNING/INFO/g' /etc/kytos/logging.ini

test -z "$TESTS" && TESTS=tests/

python3 scripts/wait_for_mongo.py 2>/dev/null
#python3 -m pytest --capture=tee-sys tests/test_e2e_31_of_lldp_loop_detection.py::TestE2EOfLLDPLoopDetection::test_001_loop_detection_disable_action
#python3 -m pytest --capture=tee-sys tests/test_e2e_31_of_lldp_loop_detection.py::TestE2EOfLLDPLoopDetection::test_010_lldp_ignored_loops
python3 -m pytest --capture=tee-sys tests/test_e2e_31_of_lldp_loop_detection.py::TestE2EOfLLDPLoopDetection::test_020_reconfigure_ignored_loops

#python3 -m pytest $TESTS

#tail -f

# only run specific test
# python3 -m pytest --timeout=60 tests/test_e2e_10_mef_eline.py::TestE2EMefEline::test_on_primary_path_fail_should_migrate_to_backup
