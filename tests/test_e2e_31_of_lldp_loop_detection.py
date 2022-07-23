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
        #cls.net.wait_switches_connect()
        #time.sleep(10)

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
        api_url = KYTOS_API + '/topology/v3/interfaces' 
        response = requests.get(api_url)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['interfaces'][interface_id]['enabled'] == True

        # WAIT for some time, until the feature kicks
        time.sleep(polling_time)

        # GET topology with the interface ensuring that it's disabled
        api_url = KYTOS_API + '/topology/v3/interfaces' 
        response = requests.get(api_url)
        assert response.status_code == 200, response.text
        data = response.json()
        assert 'looped' in data['interfaces'][interface_id]['metadata']
        assert data['interfaces'][interface_id]['enabled'] == False


    def test_010_lldp_ignored_loops(self):
        """ Test that the ports 4 and 5 are ignored. """

        polling_time = 5

        interface_id4 = "00:00:00:00:00:00:00:01:4"

        # GET topology with the interfaces ensuring that they are enabled
        api_url = KYTOS_API + '/topology/v3/interfaces' 
        response = requests.get(api_url)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['interfaces'][interface_id4]['enabled'] == True

        # WAIT for some time, until the feature kicks
        time.sleep(polling_time)

        # GET topology with the interface ensuring that they are enabled
        api_url = KYTOS_API + '/topology/v3/interfaces' 
        response = requests.get(api_url)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['interfaces'][interface_id4]['enabled'] == True  # [4,5] is an ignored loop


    def test_020_reconfigure_ignored_loops(self):
        """ Test that when we reconfigure the ignored loop with 
        POST /api/kytos/topology/v3/switches/{{dpid}}/metadata 
        the loops aren't ignored anymore.. """

        polling_time = 5

        switch = '00:00:00:00:00:00:00:01'
        interface_id4 = "00:00:00:00:00:00:00:01:4"

        # GET topology with the interfaces ensuring that they are enabled
        api_url = KYTOS_API + '/topology/v3/interfaces' 
        response = requests.get(api_url)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['interfaces'][interface_id4]['enabled'] == True

        # WAIT for some time, until the feature kicks
        time.sleep(polling_time)

        # Reconfigure the ignored loops
        api_url = KYTOS_API + '/topology/v3/switches/%s/metadata' % switch
        response = requests.post(api_url, json={"ignored_loops": []})
        assert response.status_code == 201, response.text

        self.restart()

        # GET topology with the interface ensuring that they are enabled
        api_url = KYTOS_API + '/topology/v3/interfaces' 
        response = requests.get(api_url)
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['interfaces'][interface_id4]['enabled'] == False # [4,5] is an ignored loop, it was reconfigured







        