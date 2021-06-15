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

    def test_005_install_flow_on_non_existent_switch_should_fail(self):
        """Tests if the flow installation process on an invalid
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

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:05'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 404

    def test_010_install_flow_should_fail(self):
        """Tests if the flow installation process specifying an empty
        payload behaves as expected (400 Error)."""

        payload = {}

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_015_install_flow_should_fail(self):
        """Tests if the flow installation process specifying an empty
        flow data on the payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_020_install_flow_should_fail(self):
        """Tests if the flow installation process specifying an empty
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

    def test_025_retrieve_flow_from_non_existent_switch_should_fail(self):
        """Tests if the flow retrieving process of an invalid
        switch behaves as expected (404 Error)."""

        switch_id = '00:00:00:00:00:00:00:05'

        # It tries to get a flow that does not exist
        api_url = KYTOS_API + '/flow_manager/v2/flows/' + switch_id
        response = requests.get(api_url)
        assert response.status_code == 404

    def test_030_install_flows_should_fail(self):
        """Tests if the flow installation process specifying an
        empty payload behaves as expected (400 Error)."""

        payload = {}

        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_035_install_flows_should_fail(self):
        """Tests if the flow installation process specifying an empty
        flow data on the payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_040_install_flows_should_fail(self):
        """Tests if the flow installation process specifying an empty
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

    def test_045_delete_flow_on_non_existent_switch_should_fail(self):
        """Tests if the flow deletion process specifying an
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

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:05'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 404

    def test_050_delete_flow_should_fail(self):
        """Tests if the flow deletion process specifying an
        empty payload behaves as expected (400 Error)."""

        payload = {}

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_055_delete_flow_should_fail(self):
        """Tests if the flow deletion process specifying an empty
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

    def test_060_delete_flow_should_fail(self):
        """Tests if the flow deletion process specifying an an empty
        flow data on the payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
                {

                }
            ]
        }

        # Deletes the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_065_delete_flows_should_fail(self):
        """Tests if the flow deletion process specifying an
        empty payload behaves as expected (400 Error)."""

        payload = {}

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_070_delete_flows_should_fail(self):
        """Tests if the flow deletion process specifying an empty flow
        data on the payload behaves as expected (400 Error)."""

        payload = {
            "flows": [
            ]
        }

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.delete(api_url, data=json.dumps(payload),
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_075_delete_flows_should_fail(self):
        """Tests if the flow deletion process specifying an empty flow
        data on the payload behaves as expected (400 Error)."""

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
