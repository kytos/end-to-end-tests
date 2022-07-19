import requests
from tests.helpers import NetworkTest
import time

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % CONTROLLER


class TestE2EOfLLDPLoopDetection:
    net = None

    @classmethod
    def setup_class(cls):
        cls.net = NetworkTest(CONTROLLER, topo_name='looped')
        cls.net.start()
        cls.net.restart_kytos_clean()
        cls.net.wait_switches_connect()
        time.sleep(10)

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def restart(self, _clean_config=False, _enable_all=False):

        # Start the controller setting an environment in which the setting is
        # preserved and avoid the default enabling of all elements
        self.net.start_controller(clean_config=_clean_config, enable_all=_enable_all)
        self.net.wait_switches_connect()

        # Wait a few seconds 
        time.sleep(10)

    def test_001_loop_detection_disable_action(self):
        """ This will test that given a looped topology, assuming that there is a loop
        it's going to shutdown the interface. """

        polling_time = 5

        interface_id = "00:00:00:00:00:00:00:01:1"

        # GET topology with the interface ensuring that it's enabled
        api_url = KYTOS_API + '/of_lldp/v1/interfaces/'
        response = requests.get(api_url)
        assert response.status_code == 200, response.text
        data = response.json()
        assert 'interfaces' in data
        assert data[interface_id]['enabled'] == True

        # WAIT for some time, until the feature kicks
        time.sleep(polling_time)

        # GET topology with the interface ensuring that it's disabled
        response = requests.get(api_url)
        assert response.status_code == 200, response.text
        data = response.json()
        assert 'interfaces' in data
        assert data[interface_id]['enabled'] == False


    def test_010_lldp_ignored_loops(self):
        """ Test that the ports 4 and 5 are ignored. """

        polling_time = 5

        interface_id4 = "00:00:00:00:00:00:00:01:4"
        interface_id5 = "00:00:00:00:00:00:00:01:5"

        # GET topology with the interfaces ensuring that they are enabled
        api_url = KYTOS_API + '/of_lldp/v1/interfaces/'
        response = requests.get(api_url)
        assert response.status_code == 200, response.text
        data = response.json()
        assert 'interfaces' in data
        assert data[interface_id4]['enabled'] == True
        assert data[interface_id5]['enabled'] == True

        # WAIT for some time, until the feature kicks
        time.sleep(polling_time)

        # GET topology with the interface ensuring that they are enabled
        response = requests.get(api_url)
        assert response.status_code == 200, response.text
        data = response.json()
        assert 'interfaces' in data
        assert data[interface_id4]['enabled'] == True
        assert data[interface_id5]['enabled'] == True


    def test_020_reconfigure_ignored_loops(self):
        """ Test that when we reconfigure the ignored loop with 
        POST /api/kytos/topology/v3/switches/{{dpid}}/metadata 
        the loops aren't ignored anymore.. """

        polling_time = 5

        interface_id4 = "00:00:00:00:00:00:00:01:4"
        interface_id5 = "00:00:00:00:00:00:00:01:5"

        # GET topology with the interfaces ensuring that they are enabled
        api_url = KYTOS_API + '/of_lldp/v1/interfaces/'
        response = requests.get(api_url)
        assert response.status_code == 200, response.text
        data = response.json()
        assert 'interfaces' in data
        assert data[interface_id4]['enabled'] == True
        assert data[interface_id5]['enabled'] == True

        # Reconfigure the ignored loop
        switch_id = "00:00:00:00:00:00:00:01"
        api_url = KYTOS_API + '/topology/v3/switches/%s/metadata' % switch_id
        response = requests.post(api_url, json={"ignored_loops": []})
        assert response.status_code == 200, response.text

        self.restart()

        # WAIT for some time, until the feature kicks
        time.sleep(polling_time)

        # GET topology with the interface ensuring that they are enabled
        assert data[interface_id4]['enabled'] == False
        assert data[interface_id5]['enabled'] == False







        