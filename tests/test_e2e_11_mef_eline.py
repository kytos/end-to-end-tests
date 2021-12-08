import json
import time

import pytest
import requests

from tests.helpers import NetworkTest

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % (CONTROLLER)


class TestE2EMefEline:
    net = None

    def setup_method(self, method):
        """
        It is called at the beginning of every class method execution
        """
        # Since some tests may set a link to down state, we should reset
        # the link state to up (for all links)
        self.net.config_all_links_up()
        # Start the controller setting an environment in
        # which all elements are disabled in a clean setting
        self.net.restart_kytos_clean()
        self.net.wait_switches_connect()
        time.sleep(10)

    @classmethod
    def setup_class(cls):
        cls.net = NetworkTest(CONTROLLER, topo_name='ring4')
        cls.net.start()
        cls.net.restart_kytos_clean()
        cls.net.wait_switches_connect()
        time.sleep(10)

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def test_005_on_primary_path_fail_should_migrate_to_backup(self):

        # TODO Check for false positives between uni_a switch 1 and uni_z switch 3 instead of switch 2
        """ When the primary_path is down and backup_path exists and is UP
            the circuit will change from primary_path to backup_path. """
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
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201

        time.sleep(10)

        # Command to up/down links to test if back-up path is taken
        self.net.net.configLinkStatus('s1', 's2', 'down')

        # Wait just a few seconds to give time to the controller receive and process the linkDown event
        time.sleep(10)

        # Check on the virtual switches directly for flows
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

        # Clean up
        h1.cmd('ip link del vlan101')
        h3.cmd('ip link del vlan101')

    def test_010_on_primary_path_fail_should_migrate_to_backup_with_dynamic_discovery_enabled(self):
        """ When the primary_path is down and backup_path exists and is UP
            the circuit will change from primary_path to backup_path with dynamic_discovery_enabled. """
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
            "dynamic_backup_path": True
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})

        time.sleep(10)

        # Command to disable links to test if back-up path is taken with the following command:
        self.net.net.configLinkStatus('s1', 's2', 'down')
        time.sleep(10)

        # Check on the virtual switches directly for flows
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

        # Clean up
        h1.cmd('ip link del vlan101')
        h3.cmd('ip link del vlan101')

    def test_015_evc_inter_switch_without_VLAN_tag(self):

        payload = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
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
        requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})

        time.sleep(10)

        # Command to disable links to test if back-up path is taken with the following command:
        self.net.net.configLinkStatus('s1', 's2', 'down')
        time.sleep(10)

        # Check on the virtual switches directly for flows
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

    def test_020_evc_intra_switch_without_VLAN_tag(self):

        # send evc_req and get circuit_id
        payload = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1"
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:01:2"
            }
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201

        time.sleep(10)

        # Check on the virtual switches directly for flows.
        s1, s2, s3, s4 = self.net.net.get('s1', 's2', 's3', 's4')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        flows_s3 = s3.dpctl('dump-flows')
        flows_s4 = s4.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 1
        assert len(flows_s3.split('\r\n ')) == 1
        assert len(flows_s4.split('\r\n ')) == 1

        # Nodes should be able to ping each other
        h1, h2 = self.net.net.get('h1', 'h2')
        h1.cmd('ip link add link %s name vlan101 type vlan id 101' % (h1.intfNames()[0]))
        h1.cmd('ip link set up vlan101')
        h1.cmd('ip addr add 101.0.0.1/24 dev vlan101')
        h2.cmd('ip link add link %s name vlan101 type vlan id 101' % (h2.intfNames()[0]))
        h2.cmd('ip link set up vlan101')
        h2.cmd('ip addr add 101.0.0.3/24 dev vlan101')
        result = h1.cmd('ping -c1 101.0.0.3')
        assert ', 0% packet loss,' in result

        # Clean up
        h1.cmd('ip link del vlan101')
        h2.cmd('ip link del vlan101')

    """It is returning 201 but should be 400 due to the presence of an only read attribute on Post (active)"""
    @pytest.mark.xfail
    def test_025_should_fail_due_to_invalid_attribute_on_payload(self):
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
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}
            ],
            "dynamic_backup_path": True,
            "active": True,
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 400
