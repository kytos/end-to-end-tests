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

    def test_010_install_flow_on_non_existent_switch_should_fail(self):
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

    def test_015_install_flow_should_fail(self):
        """Test if the flow installation process specifying an empty
        payload behaves as expected (400 Error)."""

        payload = {}

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_020_install_flow_should_fail(self):
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

    def test_025_install_flow_should_fail(self):
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
    def test_030_install_flow_should_fail(self):
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

    def test_035_retrieve_flow_from_non_existent_switch_should_fail(self):
        """Test if the flow retrieving process of an invalid
        switch behaves as expected (404 Error)."""

        switch_id = '00:00:00:00:00:00:00:05'

        # It tries to get a flow that does not exist
        api_url = KYTOS_API + '/flow_manager/v2/flows/' + switch_id
        response = requests.get(api_url)
        assert response.status_code == 404

    def test_040_install_flows_should_fail(self):
        """Test if the flow installation process specifying an empty
        payload behaves as expected (400 Error)."""

        payload = {}

        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_045_install_flows_should_fail(self):
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

    def test_050_install_flows_should_fail(self):
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
    def test_055_install_flows_should_fail(self):
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

    def test_060_delete_flow_on_non_existent_switch_should_fail(self):
        """Test if the flow deletion process specifying an invalid
        switch behaves as expected (404 Error)."""

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

    def test_065_delete_flow_should_fail(self):
        """Test if the flow deletion process specifying an empty
        payload behaves as expected (400 Error)."""

        payload = {}

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_070_delete_flow_should_fail(self):
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

    def test_075_delete_flow_should_fail(self):
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
    def test_080_delete_flow_should_fail(self):
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

    def test_085_delete_flows_should_fail(self):
        """Test if the flow deletion process specifying an empty
        payload behaves as expected (400 Error)."""

        payload = {}

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_090_delete_flows_should_fail(self):
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

    def test_095_delete_flows_should_fail(self):
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
    def test_100_delete_flows_should_fail(self):
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
