import json
import re
import time
from datetime import datetime, timedelta

import pytest
import requests

from tests.helpers import NetworkTest

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % CONTROLLER

TIME_FMT = "%Y-%m-%dT%H:%M:%S+0000"


class TestE2EMefEline:
    net = None
    evcs = {}

    def setup_method(self, method):
        """
        It is called at the beginning of every class method execution
        """
        # Start the controller setting an environment in
        # which all elements are disabled in a clean setting
        self.net.start_controller(clean_config=True, enable_all=True)
        self.net.wait_switches_connect()
        time.sleep(10)

    @classmethod
    def setup_class(cls):
        cls.net = NetworkTest(CONTROLLER)
        cls.net.start()
        cls.net.restart_kytos_clean()
        cls.net.wait_switches_connect()
        time.sleep(5)

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def create_evc(self, vlan_id, store=False):
        payload = {
            "name": "Vlan_%s" % vlan_id,
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": vlan_id}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": vlan_id}
            }
        }
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        data = response.json()
        if store:
            self.evcs[vlan_id] = data['circuit_id']
        return data['circuit_id']

    def test_010_list_evcs_should_be_empty(self):
        """Test if list circuits return 'no circuit stored.'."""
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.get(api_url)
        assert response.status_code == 200
        assert response.json() == {}

    def test_015_create_evc_intra_switch(self):
        """ create an intra-switch EVC e-line with VLAN tag
        (UNIs in the same switch) """
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
                "interface_id": "00:00:00:00:00:00:00:01:2",
                "tag": {
                    "tag_type": 1,
                    "value": 101
                }
            }
        }
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, json=payload)
        assert response.status_code == 201
        data = response.json()
        assert 'circuit_id' in data
        time.sleep(10)

        h11, h12 = self.net.net.get('h11', 'h12')
        h11.cmd('ip link add link %s name vlan101 type vlan id 101' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan101')
        h11.cmd('ip addr add 10.1.1.11/24 dev vlan101')
        h12.cmd('ip link add link %s name vlan101 type vlan id 101' % (h12.intfNames()[0]))
        h12.cmd('ip link set up vlan101')
        h12.cmd('ip addr add 10.1.1.12/24 dev vlan101')

        result = h11.cmd('ping -c1 10.1.1.12')
        assert ', 0% packet loss,' in result

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        # Each switch must have 3 flows: 01 for LLDP + 02 for the EVC (ingress + egress)
        assert len(flows_s1.split('\r\n ')) == 3

        # TODO: make sure it should be dl_vlan instead of vlan_vid
        assert 'dl_vlan=101' in flows_s1

        # clean up
        h11.cmd('ip link del vlan101')
        h12.cmd('ip link del vlan101')
        self.net.restart_kytos_clean()

    def test_020_create_evc_inter_switch(self):
        payload = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 1,
                    "value": 15
                }
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {
                    "tag_type": 1,
                    "value": 15
                }
            }
        }
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'circuit_id' in data
        time.sleep(10)

        # Each switch must have 3 flows: 01 for LLDP + 02 for the EVC (ingress + egress)
        s1, s2 = self.net.net.get('s1', 's2')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 3

        # make sure it should be dl_vlan instead of vlan_vid
        assert 'dl_vlan=15' in flows_s1
        assert 'dl_vlan=15' in flows_s2

        # Make the final and most important test: connectivity
        # 1. create the vlans and setup the ip addresses
        # 2. try to ping each other
        h11, h2 = self.net.net.get('h11', 'h2')
        h11.cmd('ip link add link %s name vlan15 type vlan id 15' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan15')
        h11.cmd('ip addr add 15.0.0.11/24 dev vlan15')
        h2.cmd('ip link add link %s name vlan15 type vlan id 15' % (h2.intfNames()[0]))
        h2.cmd('ip link set up vlan15')
        h2.cmd('ip addr add 15.0.0.2/24 dev vlan15')
        result = h11.cmd('ping -c1 15.0.0.2')
        assert ', 0% packet loss,' in result

        # clean up
        h11.cmd('ip link del vlan15')
        h2.cmd('ip link del vlan15')
        self.net.restart_kytos_clean()

    def test_025_create_evc_different_tags_each_side(self):
        payload = {
            "name": "Vlan102_103_Test",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 102}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 103}
            }
        }
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'circuit_id' in data
        time.sleep(10)

        # Each switch must have 3 flows: 01 for LLDP + 02 for the EVC (ingress + egress)
        s1, s2 = self.net.net.get('s1', 's2')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 3

        # make sure it should be dl_vlan instead of vlan_vid
        assert 'dl_vlan=102' in flows_s1
        assert 'dl_vlan=103' in flows_s2

        # Make the final and most important test: connectivity
        # 1. create the vlans and setup the ip addresses
        # 2. try to ping each other
        h11, h2 = self.net.net.get('h11', 'h2')
        h11.cmd('ip link add link %s name vlan102 type vlan id 102' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan102')
        h11.cmd('ip addr add 102.103.0.11/24 dev vlan102')
        h2.cmd('ip link add link %s name vlan103 type vlan id 103' % (h2.intfNames()[0]))
        h2.cmd('ip link set up vlan103')
        h2.cmd('ip addr add 102.103.0.2/24 dev vlan103')
        result = h11.cmd('ping -c1 102.103.0.2')
        assert ', 0% packet loss,' in result

        # clean up
        h11.cmd('ip link del vlan102')
        h2.cmd('ip link del vlan103')
        self.net.restart_kytos_clean()

    def test_030_create_evc_tag_notag(self):
        payload = {
            "name": "Vlan104_Test",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 104}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            }
        }
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'circuit_id' in data
        time.sleep(10)

        # Each switch must have 3 flows: 01 for LLDP + 02 for the EVC (ingress + egress)
        s1, s2 = self.net.net.get('s1', 's2')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 3

        # make sure it should be dl_vlan instead of vlan_vid
        assert 'dl_vlan=104' in flows_s1
        assert 'dl_vlan=104' not in flows_s2

        # Make the final and most important test: connectivity
        # 1. create the vlans and setup the ip addresses
        # 2. try to ping each other
        h11, h2 = self.net.net.get('h11', 'h2')
        h11.cmd('ip link add link %s name vlan104 type vlan id 104' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan104')
        h11.cmd('ip addr add 104.0.0.11/24 dev vlan104')
        h2.cmd('ip addr add 104.0.0.2/24 dev %s' % (h2.intfNames()[0]))
        result = h11.cmd('ping -c1 104.0.0.2')

        # make sure it should be dl_vlan instead of vlan_vid
        assert 'dl_vlan=104' in flows_s1

        # clean up
        h11.cmd('ip link del vlan104')
        h2.cmd('ip addr del 104.0.0.2/24 dev %s' % (h2.intfNames()[0]))
        self.net.restart_kytos_clean()

    def test_035_create_evc_same_vid_different_uni(self):
        # Create circuit 1
        payload = {
            "name": "Vlan110_Test",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 110}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 110}
            }
        }
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'circuit_id' in data
        evc1 = data['circuit_id']
        time.sleep(10)

        # Create circuit 2: same vlan id but in different UNIs
        payload = {
            "name": "Vlan110_Test2",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:2",
                "tag": {"tag_type": 1, "value": 110}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:03:1",
                "tag": {"tag_type": 1, "value": 110}
            }
        }
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'circuit_id' in data
        evc2 = data['circuit_id']
        assert evc1 != evc2
        time.sleep(10)

        # The switch 1 should have 5 flows: 01 for LLDP + 02 for evc1 + 02 for evc2
        # The switches 2 and 3 should have 3 flows: 01 for LLDP + 02 for each evc
        s1, s2, s3 = self.net.net.get('s1', 's2', 's3')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        flows_s3 = s3.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 5
        assert len(flows_s2.split('\r\n ')) == 3
        assert len(flows_s3.split('\r\n ')) == 3

        # make sure it should be dl_vlan instead of vlan_vid
        assert 'dl_vlan=110' in flows_s1
        assert 'dl_vlan=110' in flows_s2
        assert 'dl_vlan=110' in flows_s3

        # Make the final and most important test: connectivity
        # 1. create the vlans and setup the ip addresses
        # 2. try to ping each other
        # for evc 1:
        h11, h2 = self.net.net.get('h11', 'h2')
        h11.cmd('ip link add link %s name vlan110 type vlan id 110' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan110')
        h11.cmd('ip addr add 110.0.0.11/24 dev vlan110')
        h2.cmd('ip link add link %s name vlan110 type vlan id 110' % (h2.intfNames()[0]))
        h2.cmd('ip link set up vlan110')
        h2.cmd('ip addr add 110.0.0.2/24 dev vlan110')
        result = h11.cmd('ping -c1 110.0.0.2')
        assert ', 0% packet loss,' in result

        # for evc 2:
        h12, h3 = self.net.net.get('h12', 'h3')
        h12.cmd('ip link add link %s name vlan110 type vlan id 110' % (h12.intfNames()[0]))
        h12.cmd('ip link set up vlan110')
        h12.cmd('ip addr add 110.0.0.12/24 dev vlan110')
        h3.cmd('ip link add link %s name vlan110 type vlan id 110' % (h3.intfNames()[0]))
        h3.cmd('ip link set up vlan110')
        h3.cmd('ip addr add 110.0.0.3/24 dev vlan110')
        result = h12.cmd('ping -c1 110.0.0.3')
        assert ', 0% packet loss,' in result

        # clean up
        h11.cmd('ip link del vlan110')
        h12.cmd('ip link del vlan110')
        h2.cmd('ip link del vlan110')
        h3.cmd('ip link del vlan110')
        self.net.restart_kytos_clean()

    def test_040_disable_circuit_should_remove_openflow_rules(self):
        # let's suppose that xyz is the circuit id previously created
        # curl -X PATCH -H "Content-Type: application/json" -d '{"enable": false}' http://172.18.0.2:8181/api/kytos/mef_eline/v2/evc/xyz
        payload = {
            "name": "Vlan125_Test_evc1",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 125}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 125}
            }
        }
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'circuit_id' in data
        evc1 = data['circuit_id']
        time.sleep(10)

        # It verifies EVC's status
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['enabled'] is True

        # It disables the circuit
        payload = {"enable": False}
        response = requests.patch(api_url + evc1, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 200
        time.sleep(10)

        # It verifies EVC's status
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['enabled'] is False

        # Each switch should have only one flow: LLDP
        s1, s2 = self.net.net.get('s1', 's2')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 1
        assert len(flows_s2.split('\r\n ')) == 1

        # Nodes should not be able to ping each other
        h11, h2 = self.net.net.get('h11', 'h2')
        h11.cmd('ip link add link %s name vlan125 type vlan id 125' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan125')
        h11.cmd('ip addr add 125.0.0.11/24 dev vlan125')
        h2.cmd('ip link add link %s name vlan125 type vlan id 125' % (h2.intfNames()[0]))
        h2.cmd('ip link set up vlan125')
        h2.cmd('ip addr add 125.0.0.2/24 dev vlan125')
        result = h11.cmd('ping -c1 125.0.0.2')
        assert ', 100% packet loss,' in result

        # Clean up
        h11.cmd('ip link del vlan125')
        h2.cmd('ip link del vlan125')

    def test_045_create_circuit_reusing_same_vlanid_from_previous_evc(self):
        payload = {
            "name": "Vlan125_Test_evc1",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 125}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 125}
            }
        }
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'circuit_id' in data
        evc1 = data['circuit_id']
        time.sleep(10)

        # Delete the circuit
        api_url += evc1
        response = requests.delete(api_url)
        assert response.status_code == 200
        time.sleep(10)

        # try to reuse the vlan id
        payload = {
            "name": "Vlan125_Test_evc2",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 125}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 125}
            }
        }
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'circuit_id' in data
        evc2 = data['circuit_id']
        assert evc1 != evc2
        time.sleep(10)

        # The switches should have 3 flows: 01 for LLDP + 02 for each evc
        s1, s2 = self.net.net.get('s1', 's2')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 3

        # Nodes should be able to ping each other
        h11, h2 = self.net.net.get('h11', 'h2')
        h11.cmd('ip link add link %s name vlan125 type vlan id 125' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan125')
        h11.cmd('ip addr add 125.0.0.11/24 dev vlan125')
        h2.cmd('ip link add link %s name vlan125 type vlan id 125' % (h2.intfNames()[0]))
        h2.cmd('ip link set up vlan125')
        h2.cmd('ip addr add 125.0.0.2/24 dev vlan125')
        result = h11.cmd('ping -c1 125.0.0.2')
        assert ', 0% packet loss,' in result

        # clean up
        h11.cmd('ip link del vlan125')
        h2.cmd('ip link del vlan125')
        self.net.restart_kytos_clean()

    def test_050_on_primary_path_fail_should_migrate_to_backup(self):
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
                "interface_id": "00:00:00:00:00:00:00:03:1",
                "tag": {
                    "tag_type": 1,
                    "value": 101
                }
            },
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:02:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:2"}}
            ],
            "backup_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:3"}}
            ]
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201

        time.sleep(10)

        # Check on the virtual switches directly for flows
        s1, s2, s3 = self.net.net.get('s1', 's2', 's3')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        flows_s3 = s3.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 3
        assert len(flows_s3.split('\r\n ')) == 3

        # Command to up/down links to test if back-up path is taken
        self.net.net.configLinkStatus('s1', 's2', 'down')

        # Wait just a few seconds to give time to the controller receive and process the linkDown event
        time.sleep(10)

        # Nodes should be able to ping each other
        h11, h3 = self.net.net.get('h11', 'h3')
        h11.cmd('ip link add link %s name vlan101 type vlan id 101' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan101')
        h11.cmd('ip addr add 101.0.0.1/24 dev vlan101')
        h3.cmd('ip link add link %s name vlan101 type vlan id 101' % (h3.intfNames()[0]))
        h3.cmd('ip link set up vlan101')
        h3.cmd('ip addr add 101.0.0.3/24 dev vlan101')
        result = h11.cmd('ping -c1 101.0.0.3')
        assert ', 0% packet loss,' in result

        # Clean up
        h11.cmd('ip link del vlan101')
        h3.cmd('ip link del vlan101')

        # # Check on the virtual switches directly for flows
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        flows_s3 = s3.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 1
        assert len(flows_s3.split('\r\n ')) == 3

        # Command to up/down links to test if back-up path is taken
        self.net.net.configLinkStatus('s1', 's2', 'up')

    """It is returning Response 500, should be 200
        on delete circuit action"""
    @pytest.mark.xfail
    def test_055_delete_evc_after_restart_kytos_and_no_switch_reconnected(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        # restart the controller and change the port on purpose to avoid switches to connect
        self.net.start_controller(clean_config=False, enable_all=True, port=9999)
        time.sleep(10)

        # Delete the circuit
        response = requests.delete(api_url + evc1)
        assert response.status_code == 200
        time.sleep(10)

        response = requests.get(api_url)
        assert response.status_code == 200
        data = response.json()
        assert evc1 not in data

        response = requests.get(api_url, params={'archived': True})
        assert response.status_code == 200
        data = response.json()
        assert evc1 in data
        assert data[evc1]['archived'] is True
        assert data[evc1]['active'] is False

    # TODO
    def test_patch_evc_by_changing_unis_from_interface_to_another(self):
        """To edit an EVC, a PATCH request must be used:

        PATCH /kytos/mef_eline/v2.0/evc/<id>

        Information necessary to modify the EVC:

        {UNI_A, UNI_Z, str bandwidth, datetime start_date, datetime end_date,
        [str primary_links], [str backup_links], bool dynamic_backup_path,
        tenant, service_level}"""

        assert True

    # TODO
    def test_create_evc_with_scheduled_times_for_provisioning_and_ending(self):
        assert True

    def test_080_create_and_remove_ten_circuits_ten_times(self):
        """ Tests the creation and removal of ten circuits many times. """
        for x in range(1, 10):
            evcs = {}
            for i in range(400, 410):
                payload = {
                    "name": "evc_%s" % i,
                    "enabled": True,
                    "dynamic_backup_path": True,
                    "uni_a": {
                        "interface_id": "00:00:00:00:00:00:00:01:1",
                        "tag": {"tag_type": 1, "value": i}
                    },
                    "uni_z": {
                        "interface_id": "00:00:00:00:00:00:00:02:1",
                        "tag": {"tag_type": 1, "value": i}
                    }
                }
                api_url = KYTOS_API + '/mef_eline/v2/evc/'
                response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
                assert response.status_code == 201
                data = response.json()
                assert 'circuit_id' in data
                evcs[i] = data['circuit_id']

            time.sleep(10)

            # make sure the evcs are active and the flows were created
            s1, s2 = self.net.net.get('s1', 's2')
            flows_s1 = s1.dpctl('dump-flows')
            flows_s2 = s2.dpctl('dump-flows')
            for vid in evcs:
                evc_id = evcs[vid]
                api_url = KYTOS_API + '/mef_eline/v2/evc/' + evc_id
                response = requests.get(api_url)
                assert response.status_code == 200
                evc = response.json()
                # should be active
                assert evc["active"] is True
                # search for the vlan id
                assert "dl_vlan=%s" % vid in flows_s1
                assert "dl_vlan=%s" % vid in flows_s2
                # search for the cookie, should have two flows
                assert len(re.findall(evc['id'], flows_s1, flags=re.IGNORECASE)) == 2, "round=%d - should have 2 flows but had: \n%s" % (x, flows_s1)
                assert len(re.findall(evc['id'], flows_s2, flags=re.IGNORECASE)) == 2, "round=%d - should have 2 flows but had: \n%s" % (x, flows_s2)

            # Delete the circuits
            for vid in evcs:
                evc_id = evcs[vid]
                api_url = KYTOS_API + '/mef_eline/v2/evc/' + evc_id
                response = requests.delete(api_url)
                assert response.status_code == 200

            time.sleep(10)

            # make sure the circuits were deleted
            api_url = KYTOS_API + '/mef_eline/v2/evc/'
            response = requests.get(api_url)
            assert response.status_code == 200
            assert response.json() == {}
            flows_s1 = s1.dpctl('dump-flows')
            flows_s2 = s2.dpctl('dump-flows')
            assert len(flows_s1.split('\r\n ')) == 1, "round=%d - should have only 1 flow but had: \n%s" % (x, flows_s1)
            assert len(flows_s2.split('\r\n ')) == 1, "round=%d - should have only 1 flow but had: \n%s" % (x, flows_s2)

    def test_085_create_and_remove_ten_circuit_concurrently(self):
        """
        Tests the performance and race condition with
        the creation of multiple circuits using threading
        """
        import threading
        threads = list()
        for i in range(400, 410):
            t = threading.Thread(target=self.create_evc, args=(i, True))
            threads.append(t)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # make sure the evcs are active and the flows were created
        s1, s2 = self.net.net.get('s1', 's2')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        for vid in self.evcs:

            api_url = KYTOS_API + '/mef_eline/v2/evc/' + self.evcs[vid]
            response = requests.get(api_url)
            assert response.status_code == 200
            evc = response.json()
            # should be active
            assert evc["active"] is True

            # search for the vlan id
            assert "dl_vlan=%s" % vid in flows_s1
            assert "dl_vlan=%s" % vid in flows_s2
            # search for the cookie, should have two flows
            assert len(re.findall(evc['id'], flows_s1, flags=re.IGNORECASE)) == 2, \
                "should have 2 flows but had: \n%s" % flows_s1
            assert len(re.findall(evc['id'], flows_s2, flags=re.IGNORECASE)) == 2, \
                "should have 2 flows but had: \n%s" % flows_s2

        # Delete the circuits
        for vid in self.evcs:
            evc_id = self.evcs[vid]
            api_url = KYTOS_API + '/mef_eline/v2/evc/' + evc_id
            response = requests.delete(api_url)
            assert response.status_code == 200

        time.sleep(10)

        # make sure the circuits were deleted
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.get(api_url)
        assert response.status_code == 200
        assert response.json() == {}
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 1, "should have only 1 flow but had: \n%s" % flows_s1
        assert len(flows_s2.split('\r\n ')) == 1, "should have only 1 flow but had: \n%s" % flows_s2

    # Error (Patch returns: name can't be be updated)
    @pytest.mark.xfail
    def test_090_patch_evc_new_name(self):

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        # It verifies EVC's name
        response = requests.get(api_url + evc1)
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Vlan_100'

        payload = {"name": "My EVC_100"}

        # It sets a new name
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 200

        time.sleep(10)

        # It verifies EVC's new name
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['name'] == 'My EVC_100'

    # Error (Patch returns: uni_a can't be be updated.)
    @pytest.mark.xfail
    def test_095_patch_evc_new_unis(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:2"
            }
        }

        # It sets a new interface_id
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 200

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['uni_a']['interface_id'] == "00:00:00:00:00:00:00:01:2"

    # Error (Patch returns: uni_z can't be be updated.)
    @pytest.mark.xfail
    def test_100_patch_evc_new_unis(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:2"
            }
        }

        # It sets a new interface_id
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 200

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['uni_z']['interface_id'] == "00:00:00:00:00:00:00:02:2"

    def test_105_patch_start_date(self):

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        start_delay = 60
        start = datetime.now() + timedelta(minutes=start_delay)

        payload = {
            "start_date": start.strftime(TIME_FMT)
        }

        # It sets a new circuit's start_date
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 200

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['start_date'] == start.strftime(TIME_FMT)

    def test_110_patch_end_date(self):

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        end_delay = 60
        end_date = datetime.now() + timedelta(minutes=end_delay)

        payload = {
            "end_date": end_date.strftime(TIME_FMT)
        }

        # It sets a new circuit's end_date
        requests.patch(api_url + evc1, data=json.dumps(payload),
                       headers={'Content-type': 'application/json'})
        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['end_date'] == end_date.strftime(TIME_FMT)

    def test_115_patch_bandwidth(self):

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        bandwidth = 40
        payload = {
            "bandwidth": bandwidth
        }

        # It sets a new circuit's bandwidth
        requests.patch(api_url + evc1, data=json.dumps(payload),
                       headers={'Content-type': 'application/json'})
        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['bandwidth'] == bandwidth

        requests.delete(api_url + evc1)

    def test_120_patch_priority(self):

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        priority = 100
        payload = {
            "priority": priority
        }

        # It sets a new circuit's priority
        requests.patch(api_url + evc1, data=json.dumps(payload),
                       headers={'Content-type': 'application/json'})

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['priority'] == priority

        s1, s2 = self.net.net.get('s1', 's2')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        assert 'priority=100' in flows_s1
        assert 'priority=100' in flows_s2

    """It does not contain the queue information in the flow description"""
    @pytest.mark.xfail
    def test_125_patch_queue_id(self):

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        queue_id = 3
        payload = {
            "queue_id": queue_id
        }

        # It sets a new circuit's queue_id
        requests.patch(api_url + evc1, data=json.dumps(payload),
                       headers={'Content-type': 'application/json'})

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['queue_id'] == queue_id

        s1, s2 = self.net.net.get('s1', 's2')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')

        assert 'set_queue:3' in flows_s1
        assert 'set_queue:3' in flows_s2

    def test_130_patch_dynamic_backup_path(self):

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        dynamic_backup_path = True
        payload = {
            "dynamic_backup_path": dynamic_backup_path
        }

        # It sets a new circuit's dynamic_backup_path
        requests.patch(api_url + evc1, data=json.dumps(payload),
                       headers={'Content-type': 'application/json'})

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['dynamic_backup_path'] == dynamic_backup_path

    """The EVC is returning active=False"""
    @pytest.mark.xfail
    def test_135_patch_primary_path(self):

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            },
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:02:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:2"}}
            ]
        }
        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']
        time.sleep(10)
        payload2 = {
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}
            ]
        }
        # It sets a new circuit's primary_path
        response = requests.patch(api_url + evc1, data=json.dumps(payload2),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 200

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['primary_path'][0]['endpoint_a']['id'] == payload1['primary_path'][0]['endpoint_a']['id']
        assert data['primary_path'][0]['endpoint_b']['id'] == payload1['primary_path'][0]['endpoint_b']['id']
        assert data['active'] is True

    def test_140_patch_backup_path(self):

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
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
                "interface_id": "00:00:00:00:00:00:00:03:1",
                "tag": {
                    "tag_type": 1,
                    "value": 101
                }
            },
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:02:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:2"}}
            ],
            "backup_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:3"}}
            ]
        }
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        time.sleep(10)

        payload2 = {
            "backup_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:03:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:01:4"}}
            ]
        }

        # It sets a new circuit's backup_path
        requests.patch(api_url + evc1, data=json.dumps(payload2),
                       headers={'Content-type': 'application/json'})

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['backup_path'][0]['endpoint_a']['id'] == payload2['backup_path'][0]['endpoint_a']['id']
        assert data['backup_path'][0]['endpoint_b']['id'] == payload2['backup_path'][0]['endpoint_b']['id']

        requests.delete(api_url + evc1)

    """It is returning Response 500, should be 200"""
    @pytest.mark.xfail
    def test_145_patch_backup_links(self):

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
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
                "interface_id": "00:00:00:00:00:00:00:03:1",
                "tag": {
                    "tag_type": 1,
                    "value": 101
                }
            },
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:02:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:2"}}
            ],
            "backup_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:3"}}],
        }
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        time.sleep(10)

        payload = {
            "backup_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:02:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:2"}}
            ]
        }

        # It sets a new circuit's backup_links
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 200

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['backup_links'][0]['endpoint_a'] == payload['backup_links'][0]['endpoint_a']
        assert data['backup_links'][0]['endpoint_b'] == payload['backup_links'][0]['endpoint_b']

    """It is returning Response 500, should be 200"""
    @pytest.mark.xfail
    def test_150_patch_primary_links(self):

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
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
                "interface_id": "00:00:00:00:00:00:00:03:1",
                "tag": {
                    "tag_type": 1,
                    "value": 101
                }
            },
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:02:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:2"}}
            ],
            "primary_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:3"}}],
        }
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        time.sleep(10)

        payload = {
            "primary_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:02:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:2"}}
            ]
        }

        # It sets a new circuit's backup_links
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        # print(response)
        assert response.status_code == 200

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['primary_links'][0]['endpoint_a'] == payload['primary_links'][0]['endpoint_a']
        assert data['primary_links'][0]['endpoint_b'] == payload['primary_links'][0]['endpoint_b']

    def test_155_current_path_value_given_dynamic_backup_path_and_primary_path_conditions(self):
        payload = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}
            ]
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        time.sleep(10)

        # Command to up/down links to test if back-up path is taken
        self.net.net.configLinkStatus('s1', 's2', 'down')

        # Wait just a few seconds to give time to the controller receive and process the linkDown event
        time.sleep(10)

        current_path = [{"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                         "endpoint_b": {"id": "00:00:00:00:00:00:00:03:3"}},
                        {"endpoint_a": {"id": "00:00:00:00:00:00:00:03:2"},
                         "endpoint_b": {"id": "00:00:00:00:00:00:00:02:3"}}]

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()

        paths = []
        for _path in data['current_path']:
            paths.append({"endpoint_a": {"id": _path['endpoint_a']['id']},
                          "endpoint_b": {"id": _path['endpoint_b']['id']}})

        # Command to up/down links to test if back-up path is taken
        self.net.net.configLinkStatus('s1', 's2', 'up')

        assert paths == current_path

    def test_160_current_path_value_given_dynamic_backup_path_and_empty_primary_conditions(self):
        payload = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 100}
            }
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()

        paths = []
        for _path in data['current_path']:
            paths.append({"endpoint_a": {"id": _path['endpoint_a']['id']},
                          "endpoint_b": {"id": _path['endpoint_b']['id']}})

        current_path = [{"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                         "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}]

        assert paths == current_path

        # Command to up/down links to test if back-up path is taken
        self.net.net.configLinkStatus('s1', 's2', 'down')

        # Wait just a few seconds to give time to the controller receive and process the linkDown event
        time.sleep(10)

        current_path = [{"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                         "endpoint_b": {"id": "00:00:00:00:00:00:00:03:3"}},
                        {"endpoint_a": {"id": "00:00:00:00:00:00:00:03:2"},
                         "endpoint_b": {"id": "00:00:00:00:00:00:00:02:3"}}]

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()

        paths = []
        for _path in data['current_path']:
            paths.append({"endpoint_a": {"id": _path['endpoint_a']['id']},
                          "endpoint_b": {"id": _path['endpoint_b']['id']}})

        # Command to up/down links to test if back-up path is taken
        self.net.net.configLinkStatus('s1', 's2', 'up')

        assert paths == current_path

    def test_165_current_path_value_given_dynamic_backup_path_and_empty_primary_conditions(self):
        payload = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": False,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}
            ]
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        time.sleep(10)

        # Command to up/down links to test if back-up path is taken
        self.net.net.configLinkStatus('s1', 's2', 'down')

        # Wait just a few seconds to give time to the controller receive and process the linkDown event
        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()

        # Command to up/down links to test if back-up path is taken
        self.net.net.configLinkStatus('s1', 's2', 'up')

        assert data['active'] is False
        assert data['enabled'] is True
        assert data['current_path'] == []
