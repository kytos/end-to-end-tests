import requests
from tests.helpers import NetworkTest
import re

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % CONTROLLER

# TODO: check all the logs on the end
# TODO: persist the logs of syslog
# TODO: multiple instances or single instance for checking memory leak /
#  usage (benchmark - how many flows are supported? how many switches are supported?)


class TestE2EKytosServer:
    net = None

    def setup_method(self, method):
        """
        It is called at the beginning of the class execution
        """
        self.net = NetworkTest(CONTROLLER)
        self.net.start()
        self.net.wait_switches_connect()
        print("setup_method")

    def teardown_method(self, method):
        """
        It is called everytime a method ends it execution
        """
        self.net.stop()
        print("teardown_method")

    def test_start_kytos_api_core(self):

        # Check server status if it is UP and running
        api_url = KYTOS_API+'/core/status/'
        response = requests.get(api_url)
        assert response.status_code == 200

        data = response.json()
        assert data['response'] == 'running'

        # check the list of enabled napps
        expected_napps = [
                ("kytos", "pathfinder"),
                ("kytos", "mef_eline"),
                ("kytos", "maintenance"),
                ("kytos", "storehouse"),
                ("kytos", "flow_manager"),
                ("kytos", "of_core"),
                ("kytos", "topology"),
                ("kytos", "of_lldp")
            ]
        api_url = KYTOS_API+'/core/napps_enabled/'
        response = requests.get(api_url)
        assert response.status_code == 200

        data = response.json()
        # mef_eline is not running
        # I had to modify the output to reformat unicode strings
        # s1 = set([tuple(map(str, lst)) for lst in data['napps']])
        # s2 = set(expected_napps)
        assert set([tuple(lst) for lst in data['napps']]) == set(expected_napps)

        # Check disable a napp
        api_url = KYTOS_API+'/core/napps/kytos/mef_eline/disable'
        response = requests.get(api_url)
        assert response.status_code == 200

        api_url = KYTOS_API+'/core/napps_enabled/'
        response = requests.get(api_url)
        assert response.status_code == 200

        data = response.json()
        # s1 = set([tuple(lst) for lst in data['napps']])
        # s2 = set(expected_napps)
        # s3 = set([("kytos", "mef_eline")])
        # print(s3)
        assert set([tuple(lst) for lst in data['napps']]) == set(expected_napps) - set([("kytos", "mef_eline")])

        # Restart kytos and check if the switches are still enabled
        self.net.start_controller(clean_config=False)
        self.net.wait_switches_connect()

        api_url = KYTOS_API+'/core/napps_enabled/'
        response = requests.get(api_url)
        assert response.status_code == 200

        data = response.json()
        # s1 = set([tuple(lst) for lst in data['napps']])
        # print(s1)
        # s2 = set(expected_napps)
        # print(s2)
        # s3 = set([("kytos", "mef_eline")])
        # print(s3)
        assert set([tuple(lst) for lst in data['napps']]) == set(expected_napps) - set([("kytos", "mef_eline")])

        # check enable a napp
        api_url = KYTOS_API+'/core/napps/kytos/mef_eline/enable'
        response = requests.get(api_url)
        assert response.status_code == 200

        api_url = KYTOS_API+'/core/napps_enabled/'
        response = requests.get(api_url)
        assert response.status_code == 200

        data = response.json()
        assert set([tuple(lst) for lst in data['napps']]) == set(expected_napps)

    # test auth api
    # TODO

    def test_start_kytos_without_errors(self):
        with open('/var/log/syslog', "r") as f:
            assert re.findall('kytos.*(error|exception)', f.read(), re.I) == []
