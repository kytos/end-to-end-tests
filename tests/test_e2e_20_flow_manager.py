import json
import time

import requests

from tests.helpers import NetworkTest

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % CONTROLLER


class TestE2EFlowManager:
    net = None

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
        cls.net.wait_switches_connect()
        time.sleep(10)

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def test_005_install_flow(self):
        """Tests if, after kytos restart, a flow installed
        to a switch will still be installed."""

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "idle_timeout": 360,
                    "hard_timeout": 1200,
                    "match": {
                        "in_port": 1
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'FlowMod Messages Sent' in data['response']

        # wait for the flow to be installed
        time.sleep(10)

        # restart controller keeping configuration
        self.net.start_controller(enable_all=True, del_flows=True)
        self.net.wait_switches_connect()

        time.sleep(10)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=output:"s1-eth2"' in flows_s1

    def test_010_install_flow_and_retrieve_it_back(self):
        """Tests the flow status through the
        API's call after its installation."""

        switch_id = '00:00:00:00:00:00:00:01'

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "idle_timeout": 360,
                    "hard_timeout": 1200,
                    "match": {
                        "in_port": 1
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                }
            ]
        }

        # It installs the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows/' + switch_id
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(10)

        # restart controller keeping configuration
        self.net.start_controller(enable_all=True, del_flows=True)
        self.net.wait_switches_connect()

        time.sleep(10)

        response = requests.get(api_url)
        assert response.status_code == 200
        data = response.json()
        assert len(data[switch_id]["flows"]) == 2
        assert data[switch_id]["flows"][1]["instructions"][0]["instruction_type"] == "apply_actions"
        assert data[switch_id]["flows"][1]['instructions'][0]["actions"] == payload["flows"][0]["actions"]
        assert data[switch_id]["flows"][1]["match"] == payload["flows"][0]["match"]
        assert data[switch_id]["flows"][1]["priority"] == payload["flows"][0]["priority"]
        assert data[switch_id]["flows"][1]["idle_timeout"] == payload["flows"][0]["idle_timeout"]
        assert data[switch_id]["flows"][1]["hard_timeout"] == payload["flows"][0]["hard_timeout"]

    def test_015_install_flows(self):
        """Tests if, after kytos restart, a flow installed
        to all switches will still be installed."""

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "idle_timeout": 360,
                    "hard_timeout": 1200,
                    "match": {
                        "in_port": 1
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'FlowMod Messages Sent' in data['response']

        # wait for the flow to be installed
        time.sleep(10)

        # restart controller keeping configuration
        self.net.start_controller(enable_all=True, del_flows=True)
        self.net.wait_switches_connect()

        time.sleep(10)

        for sw_name in ['s1', 's2', 's3']:
            sw = self.net.net.get(sw_name)
            flows_sw = sw.dpctl('dump-flows')
            assert len(flows_sw.split('\r\n ')) == 2
            assert 'actions=output:"%s-eth2"' % sw_name in flows_sw

    def test_020_delete_flow(self):
        """Tests if, after kytos restart, a flow deleted
        from a switch will still be deleted."""

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "idle_timeout": 360,
                    "hard_timeout": 1200,
                    "match": {
                        "in_port": 1
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(10)

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'FlowMod Messages Sent' in data['response']

        # wait for the flow to be deleted
        time.sleep(10)

        # restart controller keeping configuration
        self.net.start_controller(enable_all=True, del_flows=True)
        self.net.wait_switches_connect()

        time.sleep(10)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 1
        assert 'actions=output:"s1-eth2"' not in flows_s1

    def test_025_delete_flows(self):
        """Tests if, after kytos restart, a flow deleted
        from all switches will still be deleted."""

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "idle_timeout": 360,
                    "hard_timeout": 1200,
                    "match": {
                        "in_port": 1
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows'
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(10)

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'FlowMod Messages Sent' in data['response']

        # wait for the flow to be deleted
        time.sleep(10)

        # restart controller keeping configuration
        self.net.start_controller(enable_all=True, del_flows=True)
        self.net.wait_switches_connect()

        time.sleep(10)

        for sw_name in ['s1', 's2', 's3']:
            sw = self.net.net.get(sw_name)
            flows_sw = sw.dpctl('dump-flows')
            assert len(flows_sw.split('\r\n ')) == 1
            assert 'actions=output:"%s-eth2"' % sw_name not in flows_sw

    def modify_match(self, restart_kytos=False):
        """Tests if after a match is modified outside
        kytos, the original flow is restored."""

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "idle_timeout": 360,
                    "hard_timeout": 1200,
                    "match": {
                        "in_port": 1
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(10)

        s1 = self.net.net.get('s1')
        s1.dpctl('del-flows', 'in_port=1')
        s1.dpctl('add-flow', 'idle_timeout=360,hard_timeout=1200,priority=10,'
                             'dl_vlan=324,actions=output:1')
        if restart_kytos:
            # restart controller keeping configuration
            self.net.start_controller(enable_all=True)
            self.net.wait_switches_connect()

        time.sleep(10)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 2
        assert 'in_port="s1-eth1' in flows_s1

    def test_030_modify_match(self):
        self.modify_match()

    def test_035_modify_match_restarting(self):
        self.modify_match(restart_kytos=True)

    def replace_action_flow(self, restart_kytos=False):

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "idle_timeout": 360,
                    "hard_timeout": 1200,
                    "match": {
                        "in_port": 1
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(10)

        # Verify the flow
        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 2
        assert 'in_port="s1-eth1' in flows_s1

        # Modify the actions and verify its modification
        s1.dpctl('mod-flows', 'actions=output:3')
        flows_s1 = s1.dpctl('dump-flows')
        assert 'actions=output:"s1-eth2"' not in flows_s1
        assert 'actions=output:"s1-eth3"' in flows_s1

        if restart_kytos:
            # restart controller keeping configuration
            self.net.start_controller(enable_all=True)
            self.net.wait_switches_connect()

        time.sleep(10)

        # Check that the flow keeps the original setting
        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=output:"s1-eth3"' not in flows_s1
        assert 'in_port="s1-eth1' in flows_s1

    def test_040_replace_action_flow(self):
        self.replace_action_flow()

    def test_045_replace_action_flow_restarting(self):
        self.replace_action_flow(restart_kytos=True)

    def add_action_flow(self, restart_kytos=False):

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "idle_timeout": 360,
                    "hard_timeout": 1200,
                    "match": {
                        "in_port": 1
                    },
                    "actions": [
                        {"action_type": "output", "port": 2}
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(10)

        # Verify the flow
        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 2
        assert 'in_port="s1-eth1' in flows_s1

        s1.dpctl('add-flow', 'in_port=1,idle_timeout=360,hard_timeout=1200,priority=10,actions=strip_vlan,output:2')

        if restart_kytos:
            # restart controller keeping configuration
            self.net.start_controller(enable_all=True)
            self.net.wait_switches_connect()

        time.sleep(10)

        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=strip_vlan,' not in flows_s1
        assert 'actions=output:"s1-eth2' in flows_s1

    def test_050_add_action_flow(self):
        self.add_action_flow()

    def test_055_add_action_flow_restarting(self):
        self.add_action_flow(restart_kytos=True)

    def flow_another_table(self, restart_kytos=False):
        """Tests if, after adding a flow in another
        table outside kytos, the flow is removed."""

        s1 = self.net.net.get('s1')
        s1.dpctl('add-flow', 'table=2,in_port=1,actions=output:2')
        if restart_kytos:
            # restart controller keeping configuration
            self.net.start_controller(enable_all=True)
            self.net.wait_switches_connect()

        time.sleep(10)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 1

    def test_060_flow_another_table(self):
        self.flow_another_table()

    def test_065_flow_another_table_restarting(self):
        self.flow_another_table(restart_kytos=True)

    def flow_table_0(self, restart_kytos=False):
        """Tests if, after adding a flow in another
        table outside kytos, the flow is removed."""

        s1 = self.net.net.get('s1')
        s1.dpctl('add-flow', 'table=0,in_port=1,actions=output:2')

        if restart_kytos:
            # restart controller keeping configuration
            self.net.start_controller(enable_all=True)
            self.net.wait_switches_connect()

        time.sleep(10)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 1

    def test_070_flow_table_0(self):
        self.flow_table_0()

    def test_075_flow_table_0_restarting(self):
        self.flow_table_0(restart_kytos=True)

    def test_080_retrieve_flows(self):
        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.get(api_url)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "00:00:00:00:00:00:00:01" in data.keys()
        assert "00:00:00:00:00:00:00:02" in data.keys()
        assert "00:00:00:00:00:00:00:03" in data.keys()
        assert len(data["00:00:00:00:00:00:00:01"]["flows"]) == 1
        assert len(data["00:00:00:00:00:00:00:02"]["flows"]) == 1
        assert len(data["00:00:00:00:00:00:00:03"]["flows"]) == 1
