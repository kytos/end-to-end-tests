import unittest
import requests
from tests.helpers import NetworkTest
import os
import signal
import time

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % (CONTROLLER)


class TestE2ETopology(unittest.TestCase):
    def setUp(self):
        self.net = NetworkTest(CONTROLLER)
        self.net.start()
        self.net.wait_switches_connect()

    def tearDown(self):
        # This function tears down the whole topology.
        self.net.stop()
        # check all the logs on the end
        # TODO: persist the logs of syslog
        # TODO: multiple instances or single instance for checking memory leak / usage (benchmark - how many flows are supported? how many switches are supported?)

   def test_list_evcs_should_be_empty(self):
        """Test if list circuits return 'no circuit stored.'."""
        api_url = KYTOS_API+'/mef_eline/v2/evc/'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

#    def test_basic_mef_eline(self):
#        # create a simple EVC intra-switch
#        # patch the EVC with new name
#        # patch the EVC with new UNIs
#        # Disable EVC
#        # Enable EVC
