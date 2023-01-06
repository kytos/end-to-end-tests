#!/bin/bash

set -xe

# the settings below are intended to decrease the tests execution time (in fact, the time.sleep() calls
# depend on the values below, otherwise many tests would fail)
sed -i 's/STATS_INTERVAL = 60/STATS_INTERVAL = 7/g' /var/lib/kytos/napps/kytos/of_core/settings.py
sed -i 's/CONSISTENCY_MIN_VERDICT_INTERVAL =.*/CONSISTENCY_MIN_VERDICT_INTERVAL = 60/g' /var/lib/kytos/napps/kytos/flow_manager/settings.py
sed -i 's/LINK_UP_TIMER = 10/LINK_UP_TIMER = 1/g' /var/lib/kytos/napps/kytos/topology/settings.py
sed -i 's/DEPLOY_EVCS_INTERVAL = 60/DEPLOY_EVCS_INTERVAL = 5/g' /var/lib/kytos/napps/kytos/mef_eline/settings.py
sed -i 's/LLDP_LOOP_ACTIONS = \["log"\]/LLDP_LOOP_ACTIONS = \["disable","log"\]/' /var/lib/kytos/napps/kytos/of_lldp/settings.py
sed -i 's/LLDP_IGNORED_LOOPS = {}/LLDP_IGNORED_LOOPS = {"00:00:00:00:00:00:00:01": \[\[4, 5\]\]}/' /var/lib/kytos/napps/kytos/of_lldp/settings.py
sed -i 's/CONSISTENCY_COOKIE_IGNORED_RANGE =.*/CONSISTENCY_COOKIE_IGNORED_RANGE = [(0xdd00000000000000, 0xdd00000000000009)]/g' /var/lib/kytos/napps/kytos/flow_manager/settings.py
sed -i 's/LIVENESS_DEAD_MULTIPLIER =.*/LIVENESS_DEAD_MULTIPLIER = 3/g' /var/lib/kytos/napps/kytos/of_lldp/settings.py

# increase logging to facilitate troubleshooting
kytosd --help >/dev/null 2>&1  ## create configs at /etc/kytos from templates
sed -i 's/WARNING/INFO/g' /etc/kytos/logging.ini

test -z "$TESTS" && TESTS=tests/
test -z "$RERUNS" && RERUNS=2

python3 scripts/wait_for_mongo.py 2>/dev/null
python3 -m pytest $TESTS --reruns $RERUNS -r fEr

#tail -f

# only run specific test
# python3 -m pytest --timeout=60 tests/test_e2e_10_mef_eline.py::TestE2EMefEline::test_on_primary_path_fail_should_migrate_to_backup