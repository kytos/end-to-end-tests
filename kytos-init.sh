#!/bin/bash

set -x

# the settings below are intended to decrease the tests execution time (in fact, the time.sleep() calls
# depend on the values below, otherwise many tests would fail)
sed -i 's/STATS_INTERVAL = 60/STATS_INTERVAL = 3/g' /var/lib/kytos/napps/kytos/of_core/settings.py
sed -i 's/LINK_UP_TIMER = 10/LINK_UP_TIMER = 1/g' /var/lib/kytos/napps/kytos/topology/settings.py
sed -i 's/DEPLOY_EVCS_INTERVAL = 60/DEPLOY_EVCS_INTERVAL = 5/g' /var/lib/kytos/napps/kytos/mef_eline/settings.py
sed -i 's/BOX_RESTORE_TIMER = 0.1/BOX_RESTORE_TIMER = 0.5/' /var/lib/kytos/napps/kytos/flow_manager/settings.py

# increase logging to facilitate troubleshooting
kytosd --help >/dev/null 2>&1  ## create configs at /etc/kytos from templates
sed -i 's/WARNING/INFO/g' /etc/kytos/logging.ini

test -z "$TESTS" && TESTS=tests/

python3 -m pytest $TESTS 2>&1 | tee log-e2e-$(date +%Y%m%d%H%M%S)

# only run specific test
# python3 -m pytest --timeout=60 tests/test_e2e_10_mef_eline.py::TestE2EMefEline::test_on_primary_path_fail_should_migrate_to_backup
