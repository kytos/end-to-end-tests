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
        """Test if the flow retrieving process of an invalid
        switch behaves as expected (404 Error)."""

        switch_id = '00:00:00:00:00:00:00:05'

        # It tries to get a flow that does not exist
        api_url = KYTOS_API + '/flow_manager/v2/flows/' + switch_id
        response = requests.get(api_url)
        assert response.status_code == 404

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

    def test_021_delete_flow_on_non_existent_switch_should_fail(self):
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
