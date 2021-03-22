import unittest
import requests
from tests.helpers import NetworkTest
import os
import time
import json

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % (CONTROLLER)


class TestE2EMefEline(unittest.TestCase):
    net = None

    @classmethod
    def setUpClass(cls):
        cls.net = NetworkTest(CONTROLLER, topo_name='DanielaTopo')
        cls.net.start()
        cls.net.restart_kytos_clean()

    @classmethod
    def tearDownClass(cls):
        cls.net.stop()

    def test_on_primary_path_fail_should_migrate_to_backup(self):
        # TODO Check for false positives between uni_a switch 1 and uni_z switch 3 instead of switch 2
        """ When the primary_path is down and backup_path exists and is UP
            the circuit will change from primary_path to backup_path. """
        self.net.restart_kytos_clean()
        time.sleep(10)
        payload = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 1,
                    "value": 101
                }
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {
                    "tag_type": 1,
                    "value": 101
                }
            },
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:3"}}
            ],
            "backup_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:04:4"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:04:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:4"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:03:1"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:4"}}
            ]
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, json=payload)
        assert response.status_code == 201

        time.sleep(10)

        """ Command to up/down links to test if back-up path is taken with the following command: """
        self.net.net.configLinkStatus('s1', 's2', 'down')

        # wait just a few seconds to give time to the controller receive and process the linkDown event
        time.sleep(2)

        """Check on the virtual switches directly for flows.
        Each switch that the flow traveled must have 3 flows:
        01 for LLDP + 02 for the EVC (ingress + egress)"""
        s1, s2, s3, s4 = self.net.net.get('s1', 's2', 's3', 's4')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        flows_s3 = s3.dpctl('dump-flows')
        flows_s4 = s4.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 3
        assert len(flows_s3.split('\r\n ')) == 3
        assert len(flows_s4.split('\r\n ')) == 3

        # Nodes should be able to ping each other
        h1, h3 = self.net.net.get('h1', 'h3')
        h1.cmd('ip link add link %s name vlan101 type vlan id 101' % (h1.intfNames()[0]))
        h1.cmd('ip link set up vlan101')
        h1.cmd('ip addr add 101.0.0.1/24 dev vlan101')
        h3.cmd('ip link add link %s name vlan101 type vlan id 101' % (h3.intfNames()[0]))
        h3.cmd('ip link set up vlan101')
        h3.cmd('ip addr add 101.0.0.3/24 dev vlan101')
        result = h1.cmd('ping -c1 101.0.0.3')
        assert ', 0% packet loss,' in result

        # clean up
        h1.cmd('ip link del vlan101')
        h3.cmd('ip link del vlan101')

    def test_on_primary_path_fail_should_migrate_to_backup_with_dynamic_discovery_enabled(self):
        """ When the primary_path is down and backup_path exists and is UP
            the circuit will change from primary_path to backup_path with dynamic_discovery_enabled. """
        self.net.restart_kytos_clean()
        time.sleep(10)
        payload = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 1,
                    "value": 101
                }
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {
                    "tag_type": 1,
                    "value": 101
                }
            },
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:3"}}
            ],
            "backup_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:04:4"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:04:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:4"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:03:1"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:4"}}
            ],
            "dynamic_backup_path": "true",
            "active": "true",
            "enabled": "true"
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, json=payload)
        assert response.status_code == 201

        time.sleep(10)

        # Command to disable links to test if back-up path is taken with the following command:
        self.net.net.configLinkStatus('s1', 's2', 'down')
        time.sleep(2)

        # Check on the virtual switches directly for flows. Each switch that the flow traveled must have 3 flows:
        # 01 for LLDP + 02 for the EVC (ingress + egress)
        s1, s2, s3, s4 = self.net.net.get('s1', 's2', 's3', 's4')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        flows_s3 = s3.dpctl('dump-flows')
        flows_s4 = s4.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 3
        assert len(flows_s3.split('\r\n ')) == 3
        assert len(flows_s4.split('\r\n ')) == 3

        # Nodes should be able to ping each other
        h1, h3 = self.net.net.get('h1', 'h3')
        h1.cmd('ip link add link %s name vlan101 type vlan id 101' % (h1.intfNames()[0]))
        h1.cmd('ip link set up vlan101')
        h1.cmd('ip addr add 101.0.0.1/24 dev vlan101')
        h3.cmd('ip link add link %s name vlan101 type vlan id 101' % (h3.intfNames()[0]))
        h3.cmd('ip link set up vlan101')
        h3.cmd('ip addr add 101.0.0.3/24 dev vlan101')
        result = h1.cmd('ping -c1 101.0.0.3')
        assert ', 0% packet loss,' in result

        # clean up
        h1.cmd('ip link del vlan101')
        h3.cmd('ip link del vlan101')
        self.net.restart_kytos_clean()

    def evc_inter_switch_without_VLAN_tag(self):

        # evc_req
        payload = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1"
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:01:4"

            },
            "current_path": [],
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:3"}}
            ],
            "backup_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:04:4"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:04:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:4"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:03:1"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:4"}}
            ]
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, json=json.dumps(payload))
        self.assertEqual(response.status_code, 200)

        # Check on the virtual switches directly for flows. Each switch that the flow traveled must have 3 flows:
        # 01 for LLDP + 02 for the EVC (ingress + egress)
        s1, s2, s3, s4 = self.net.net.get('s1', 's2', 's3', 's4')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        flows_s3 = s3.dpctl('dump-flows')
        flows_s4 = s4.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 3
        assert len(flows_s3.split('\r\n ')) == 3
        assert len(flows_s4.split('\r\n ')) == 3

        # Nodes should be able to ping each other
        h1, h3 = self.net.net.get('h1', 'h3')
        h1.cmd('ip link add link %s name vlan101 type vlan id 101' % (h1.intfNames()[0]))
        h1.cmd('ip link set up vlan101')
        h1.cmd('ip addr add 101.0.0.1/24 dev vlan101')
        h3.cmd('ip link add link %s name vlan101 type vlan id 101' % (h3.intfNames()[0]))
        h3.cmd('ip link set up vlan101')
        h3.cmd('ip addr add 101.0.0.3/24 dev vlan101')
        result = h1.cmd('ping -c1 101.0.0.3')
        assert ', 0% packet loss,' in result

        # clean up
        h1.cmd('ip link del vlan101')
        h3.cmd('ip link del vlan101')
        self.net.restart_kytos_clean()

    def create_many_evc_at_once_and_verify_proper_installation(self):
        # TODO Create many EVC at once and check if they are all working (e.g., 300 EVCs in the same file)

        url = "http://localhost:8181/api/kytos/mef_eline/v2/evc/"
        vlan_start = 1
        vlan_end = 200

        vlan = vlan_start
        while vlan <= vlan_end:
            evc = {
                "Content-Type": "application/json",
                "cache-control": "no-cache",
                "name": "evc_%s" % vlan,
                "uni_a": {
                    "interface_id": "00:00:00:00:00:00:00:01:1",
                    "tag": {
                        "tag_type": 1,
                        "value": vlan
                    }
                },
                "uni_z": {
                    "interface_id": "00:00:00:00:00:00:00:02:1",
                    "tag": {
                        "tag_type": 1,
                        "value": vlan
                    }
                },
                "current_path": [],
                "primary_path": [
                    {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                     "endpoint_b": {"id": "00:00:00:00:00:00:00:02:3"}}
                ],
                "backup_path": [
                    {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                     "endpoint_b": {"id": "00:00:00:00:00:00:00:04:4"}},
                    {"endpoint_a": {"id": "00:00:00:00:00:00:00:04:3"},
                     "endpoint_b": {"id": "00:00:00:00:00:00:00:03:4"}},
                    {"endpoint_a": {"id": "00:00:00:00:00:00:00:03:1"},
                     "endpoint_b": {"id": "00:00:00:00:00:00:00:02:4"}}
                ],
                "dynamic_backup_path": "true",
                "active": "true",
                "enabled": "true"
            }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, json=json.dumps(evc))
        self.assertEqual(response.status_code, 200)

        request = requests.post(url=url, json=evc)
        circuit_id = json.loads(request.content.decode("utf-8"))

        if isinstance(circuit_id, dict):
            print("circuit_id %s created" % circuit_id['circuit_id'])

        # Check if vlan_id is inside the dump-flows. Each switch that the flow traveled must have 3 flows:
        # 01 for LLDP + 02 for the EVC (ingress + egress)
        s1, s2, s3, s4 = self.net.net.get('s1', 's2', 's3', 's4')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        flows_s3 = s3.dpctl('dump-flows')
        flows_s4 = s4.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 3
        assert len(flows_s3.split('\r\n ')) == 3
        assert len(flows_s4.split('\r\n ')) == 3

        # Clean up: Delete all EVCs & re-start Kytos fresh
        print("Removing all EVCs ...")
        evcs = requests.get(url)
        evcs = json.loads(evcs.content.decode("utf-8"))
        for evc in evcs:
            if evcs[evc]['enabled']:
                requests.delete(url=url + evc)
        print("... Done!")

        self.net.restart_kytos_clean()

    def evc_intra_switch_without_VLAN_tag(self):

        # send evc_req and get circuit_id
        payload = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1"
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:01:4"
            },
            "current_path": [],
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:1"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:01:2"}}
            ],
            "backup_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:1"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:01:3"}}
            ]
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, json=json.dumps(payload))
        self.assertEqual(response.status_code, 200)

        # Check on the virtual switches directly for flows. Each switch that the flow traveled must have 3 flows:
        # 01 for LLDP + 02 for the EVC (ingress + egress)
        s1, s2, s3, s4 = self.net.net.get('s1', 's2', 's3', 's4')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        flows_s3 = s3.dpctl('dump-flows')
        flows_s4 = s4.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 3
        assert len(flows_s3.split('\r\n ')) == 3
        assert len(flows_s4.split('\r\n ')) == 3

        #TODO: assert that evc was installed by pinging, and look for verification of the circuit id been created

        # clean up
        self.net.restart_kytos_clean()
