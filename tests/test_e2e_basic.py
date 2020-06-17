import unittest
import requests
from tests.helpers import NetworkTest
import os
import signal
import time

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % (CONTROLLER)


class TestE2EBasic(unittest.TestCase):
    def setUp(self):
        self.net = NetworkTest(CONTROLLER)
        self.net.start()
        self.net.wait_switches_connect()

    def tearDown(self):
        # This function tears down the whole topology.
        self.net.stop()

    def test_list_evcs_should_be_empty(self):
        """Test if list circuits return 'no circuit stored.'."""
        api_url = KYTOS_API+'/mef_eline/v2/evc/'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_list_switches(self):
        api_url = KYTOS_API+'/topology/v3/switches'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue('switches' in data)
        self.assertEqual(len(data['switches']), 3)
        self.assertTrue('00:00:00:00:00:00:00:01' in data['switches'])
        self.assertTrue('00:00:00:00:00:00:00:02' in data['switches'])
        self.assertTrue('00:00:00:00:00:00:00:03' in data['switches'])

    def test_enabling_disabling_switches_persistent(self):
        sw1 = '00:00:00:00:00:00:00:01'
        sw2 = '00:00:00:00:00:00:00:02'
        sw3 = '00:00:00:00:00:00:00:03'
        
        # make sure the switches are disabled by default
        api_url = KYTOS_API+'/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        print "data = ", data
        self.assertFalse(data['switches'][sw1]['enabled'])
        self.assertFalse(data['switches'][sw2]['enabled'])
        self.assertFalse(data['switches'][sw3]['enabled'])

        # enable the switches
        api_url = KYTOS_API+'/topology/v3/switches/%s/enable' % (sw1)
        response = requests.post(api_url)
        self.assertEqual(response.status_code, 201)
        api_url = KYTOS_API+'/topology/v3/switches/%s/enable' % (sw2)
        response = requests.post(api_url)
        self.assertEqual(response.status_code, 201)
        api_url = KYTOS_API+'/topology/v3/switches/%s/enable' % (sw3)
        response = requests.post(api_url)
        self.assertEqual(response.status_code, 201)

        # check if the switches are now enabled
        api_url = KYTOS_API+'/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        self.assertTrue(data['switches'][sw1]['enabled'])
        self.assertTrue(data['switches'][sw2]['enabled'])
        self.assertTrue(data['switches'][sw3]['enabled'])

        # restart kytos and check if the switches are still enabled
        with open('/var/run/kytos/kytosd.pid', "r") as f:
            pid = int(f.read())
            os.kill(pid, signal.SIGTERM)
        time.sleep(5)
        os.system('kytosd &')
        self.net.wait_switches_connect()

        # check if the switches are still enabled and now with the links
        api_url = KYTOS_API+'/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        self.assertTrue(data['switches'][sw1]['enabled'])
        self.assertTrue(data['switches'][sw2]['enabled'])
        self.assertTrue(data['switches'][sw3]['enabled'])

#    def test_enabling_disabling_ports_persistent(self)
#        # /api/kytos/topology/v3/switches --> check if it is disabled
#        # /v3/switches/{dpid}/enable
#        # /api/kytos/topology/v3/switches --> check if it is enabled
#        # kill kytosd and restart, check if switches are still enabled
#        # check topology discovery

#    def test_enabling_disabling_links_persistent(self)
#        # /api/kytos/topology/v3/switches --> check if it is disabled
#        # /v3/switches/{dpid}/enable
#        # /api/kytos/topology/v3/switches --> check if it is enabled
#        # kill kytosd and restart, check if switches are still enabled
#        # check topology discovery

#    def test_all_enabled_should_activate_topology_discovery(self)
#        # /api/kytos/topology/v3/switches --> check if it is disabled
#        # /v3/switches/{dpid}/enable
#        # /api/kytos/topology/v3/switches --> check if it is enabled
#        # kill kytosd and restart, check if switches are still enabled
#        # check topology discovery

#    def test_basic_mef_eline(self):
#        # create a simple EVC intra-switch
#        # patch the EVC with new name
#        # patch the EVC with new UNIs
#        # Disable EVC
#        # Enable EVC
