import unittest
import requests
from tests.helpers import NetworkTest
import os
import signal
import time
import re

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % (CONTROLLER)


class TestE2EKytosServer(unittest.TestCase):
    # TODO: check all the logs on the end
    # TODO: persist the logs of syslog
    # TODO: multiple instances or single instance for checking memory leak / usage (benchmark - how many flows are supported? how many switches are supported?)
    def setUp(self):
        self.net = NetworkTest(CONTROLLER)
        self.net.start()
        self.net.wait_switches_connect()

    def tearDown(self):
        # This function tears down the whole topology.
        self.net.stop()

    def test_start_kytos_api_core(self):
        # check server status if it is UP and running
        api_url = KYTOS_API+'/core/status/'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['response'], 'running')

        # check the list of enabled napps
        expected_napps = [
                ["kytos", "pathfinder"], 
                ["kytos", "mef_eline"], 
                ["kytos", "storehouse"], 
                ["kytos", "flow_manager"], 
                ["kytos", "of_core"], 
                ["kytos", "topology"], 
                ["kytos", "of_lldp"]
            ]
        api_url = KYTOS_API+'/core/napps_enabled/'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['napps'], expected_napps)

        # check disable a napp
        api_url = KYTOS_API+'/core/napps/kytos/mef_eline/disable'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        api_url = KYTOS_API+'/core/napps_enabled/'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['napps'], expected_napps[:1] + expected_napps[2:])

        # restart kytos and check if the napp is still disabled
        with open('/var/run/kytos/kytosd.pid', "r") as f:
            pid = int(f.read())
            os.kill(pid, signal.SIGTERM)
        time.sleep(5)
        os.system('kytosd &')
        self.net.wait_switches_connect()
        api_url = KYTOS_API+'/core/napps_enabled/'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['napps'], expected_napps[:1] + expected_napps[2:])

        # check enable a napp
        api_url = KYTOS_API+'/core/napps/kytos/mef_eline/enable'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        api_url = KYTOS_API+'/core/napps_enabled/'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['napps'], expected_napps)

        # test auth api
        # TODO

    def test_start_kytos_without_errors(self):
        with open('/var/log/syslog', "r") as f:
            self.assertEqual(re.findall('kytos.*(error|exception)', f.read(), re.I), [])
