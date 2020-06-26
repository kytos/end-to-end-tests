import unittest
import requests
from tests.helpers import NetworkTest
import os
import time
import json

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % (CONTROLLER)


class TestE2ETopology(unittest.TestCase):
    net = None
    @classmethod
    def setUpClass(cls):
        cls.net = NetworkTest(CONTROLLER)
        cls.net.start()
        cls.net.wait_switches_connect()

    @classmethod
    def tearDownClass(cls):
        cls.net.stop()

    def test_list_evcs_should_be_empty(self):
        """Test if list circuits return 'no circuit stored.'."""
        api_url = KYTOS_API+'/mef_eline/v2/evc/'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_create_evc_intra_switch(self):
        # TODO
        self.assertTrue(True)

    def test_create_evc_inter_switch(self):
        payload = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 1,
                    "value": 100
                }
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {
                    "tag_type": 1,
                    "value": 100
                }
            }
        }
        api_url = KYTOS_API+'/mef_eline/v2/evc/'
        response = requests.post(api_url, json=json.dumps(payload))
        self.assertEqual(response.status_code, 201)

        h1, h2 = self.net.get( 'h1', 'h2' )
        result = h1.cmd( 'ping -c1', h2.IP() )
        self.assertIn(', 0% packet loss,', result)
        data = response.json()
        self.assertIn('circuit_id', data)

        s1, s2 = self.net.get( 's1', 's2' )
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        # Each switch must have 3 flows: 01 for LLDP + 02 for the EVC (ingress + egress)
        self.assertEqual(len(flows_s1.split('\r\n ')), 3)
        self.assertEqual(len(flows_s2.split('\r\n ')), 3)

        # TODO: make sure it should be dl_vlan instead of vlan_vid
        self.assertIn('dl_vlan=100', flows_s1)
        self.assertIn('dl_vlan=100', flows_s2)

    def test_patch_evc_new_name(self):
        # TODO
        self.assertTrue(True)

    def test_patch_evc_new_unis(self):
        # TODO
        self.assertTrue(True)

    def test_disable_evc(self):
        # TODO
        self.assertTrue(True)

    def test_on_primary_path_fail_should_migrate_to_backup(self):
        # TODO
        self.assertTrue(True)
