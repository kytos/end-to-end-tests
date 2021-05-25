import json
import pytest
import requests
from tests.helpers import NetworkTest
import time

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

    def test_010_install_flow(self):
        """Test if, after kytos restart, a flow installed
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

    def test_011_install_flow_and_retrieve_it_back(self):
        """Test the flow status through the
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

        response = requests.get(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert len(data[switch_id]["flows"]) == 2
        assert data[switch_id]["flows"][1]["actions"] == payload["flows"][0]["actions"]
        assert data[switch_id]["flows"][1]["match"] == payload["flows"][0]["match"]
        assert data[switch_id]["flows"][1]["priority"] == payload["flows"][0]["priority"]
        assert data[switch_id]["flows"][1]["idle_timeout"] == payload["flows"][0]["idle_timeout"]
        assert data[switch_id]["flows"][1]["hard_timeout"] == payload["flows"][0]["hard_timeout"]

    def test_012_install_flow_on_non_existent_switch_should_fail(self):
        """Test if the flow installation process on an
        invalid switch behaves as expected (404 Error)."""

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

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:05'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 404

    """
    The Api call is returning 200 when should be 400
    Issue https://github.com/kytos/flow_manager/issues/134
    """
    @pytest.mark.xfail
    def test_0131_install_flow_should_fail(self):
        """Test if the flow installation process specifying an empty
        payload behaves as expected (400 Error)."""

        payload = {}

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call is returning 200 when should be 400
    Issue https://github.com/kytos/flow_manager/issues/134
    """
    @pytest.mark.xfail
    def test_0132_install_flow_should_fail(self):
        """Test if the flow installation process specifying an empty
        flow data on the payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call is returning 200 when should be 400
    Issue https://github.com/kytos/flow_manager/issues/134
    """
    @pytest.mark.xfail
    def test_0133_install_flow_should_fail(self):
        """Test if the flow installation process specifying an empty
        flow data on the payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
                {

                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The execution breaks when should be returning a 400
    Issue https://github.com/kytos/flow_manager/issues/134
    """
    @pytest.mark.xfail
    def test_0134_install_flow_should_fail(self):
        """Test if the flow installation process specifying a
        wrong datatype payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
                {
                    "priority"
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call is returning 500 when should be 404
    Issue https://github.com/kytos/flow_manager/issues/131
    """
    @pytest.mark.xfail
    def test_014_retrieve_flow_from_non_existent_switch_should_fail(self):
        """Test if the flow retrieving process of an unknown
        path behaves as expected (404 Error)."""

        switch_id = '00:00:00:00:00:00:00:05'

        # It tries to get a flow that does not exist
        api_url = KYTOS_API + '/flow_manager/v2/flows/' + switch_id
        response = requests.get(api_url)
        assert response.status_code == 404

    def test_015_install_flows(self):
        """Test if, after kytos restart, a flow installed to all switches will
           still be installed."""

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

    """
    The Api call is returning 200 when should be 400
    Issue https://github.com/kytos/flow_manager/issues/132
    """
    @pytest.mark.xfail
    def test_016_install_flows_should_fail(self):
        """Test if the flow installation process specifying an empty
        payload behaves as expected (400 Error)."""

        payload = {}

        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call is returning 200 when should be 400
    Issue https://github.com/kytos/flow_manager/issues/132
    """
    @pytest.mark.xfail
    def test_017_install_flows_should_fail(self):
        """Test if the flow installation process specifying an empty
        flow data on the payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call is returning 200 when should be 400
    Issue https://github.com/kytos/flow_manager/issues/132
    """
    @pytest.mark.xfail
    def test_018_install_flows_should_fail(self):
        """Test if the flow installation process specifying an empty
        flow data on the payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
                {

                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call fails on runtime when should return a 400
    Issue https://github.com/kytos/flow_manager/issues/132
    """
    @pytest.mark.xfail
    def test_019_install_flows_should_fail(self):
        """Test if the flow installation process specifying a
        wrong datatype payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
                {
                    "priority"
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_020_delete_flow(self):
        """Test if, after kytos restart, a flow deleted from a switch will
           still be deleted."""

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

    def test_021_delete_flow_on_non_existent_path_should_fail(self):
        """Test if the flow deletion process specifying an unknown
        path behaves as expected (404 Error)."""

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

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:05'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 404

    """
    The Api call is returning 200 when should be 400
    Issue https://github.com/kytos/flow_manager/issues/136
    """
    @pytest.mark.xfail
    def test_022_delete_flow_should_fail(self):
        """Test if the flow deletion process specifying an empty
        payload behaves as expected (400 Error)."""

        payload = {}

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call is returning 200 when should be 400
    Issue https://github.com/kytos/flow_manager/issues/136
    """
    @pytest.mark.xfail
    def test_023_delete_flow_should_fail(self):
        """Test if the flow deletion process specifying an empty
        flow data on the payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
            ]
        }

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call is returning 200 when should be 400
    Issue https://github.com/kytos/flow_manager/issues/136
    """
    @pytest.mark.xfail
    def test_024_delete_flow_should_fail(self):
        """Test if the flow deletion process specifying an an empty
        flow data on the payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
                {

                }
            ]
        }

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call fails on runtime when should return a 400
    Issue https://github.com/kytos/flow_manager/issues/136
    """
    @pytest.mark.xfail
    def test_0241_delete_flow_should_fail(self):
        """Test if the flow deletion process specifying a
        wrong datatype payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
                {
                    "priority"
                }
            ]
        }

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_025_delete_flows(self):
        """Test if, after kytos restart, a flow deleted from all switches will
           still be deleted."""

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

    """
    The Api call is returning 200 when should be 400
    Issue https://github.com/kytos/flow_manager/issues/135
    """
    @pytest.mark.xfail
    def test_026_delete_flows_should_fail(self):
        """Test if the flow deletion process specifying an empty
        payload behaves as expected (400 Error)."""

        payload = {}

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call is returning 200 when should be 400
    Issue https://github.com/kytos/flow_manager/issues/135
    """
    @pytest.mark.xfail
    def test_027_delete_flows_should_fail(self):
        """Test if the flow deletion process specifying an empty
        flow data on the payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
            ]
        }

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call is returning 200 when should be 400
    Issue https://github.com/kytos/flow_manager/issues/135
    """
    @pytest.mark.xfail
    def test_028_delete_flows_should_fail(self):
        """Test if the flow deletion process specifying an empty
        flow data on the payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
                {

                }
            ]
        }

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call fails on runtime when should return a 400
    Issue https://github.com/kytos/flow_manager/issues/135
    """
    @pytest.mark.xfail
    def test_029_delete_flows_should_fail(self):
        """Test if the flow deletion process specifying a
        wrong datatype payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
                {
                    "priority"
                }
            ]
        }

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def modify_match(self, restart_kytos=False):
        """Test if after a match is modified outside kytos, the original
           flow is restored."""

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
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'FlowMod Messages Sent' in data['response']

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
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'FlowMod Messages Sent' in data['response']

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
        """Test if, after adding a flow in another table outside kytos, the
            flow is removed."""

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
        """Test if, after adding a flow in another table outside kytos, the
            flow is removed."""

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
