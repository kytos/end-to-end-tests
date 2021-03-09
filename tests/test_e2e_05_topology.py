import pytest
import json
import unittest
import requests
from tests.helpers import NetworkTest
import os
import time

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % (CONTROLLER)


class TestE2ETopology(unittest.TestCase):
    net = None
    @classmethod
    def setUpClass(cls):
        cls.net = NetworkTest(CONTROLLER)
        cls.net.start()
        cls.net.wait_switches_connect()

    @classmethod
    def tearDownClass(cls):
        cls.net.stop()

    def test_010_list_switches(self):
        api_url = KYTOS_API+'/topology/v3/switches'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue('switches' in data)
        self.assertEqual(len(data['switches']), 3)
        self.assertTrue('00:00:00:00:00:00:00:01' in data['switches'])
        self.assertTrue('00:00:00:00:00:00:00:02' in data['switches'])
        self.assertTrue('00:00:00:00:00:00:00:03' in data['switches'])

    def test_020_enabling_switch_persistent(self):
        sw1 = '00:00:00:00:00:00:00:01'
        sw2 = '00:00:00:00:00:00:00:02'
        sw3 = '00:00:00:00:00:00:00:03'

        # make sure the switches are disabled by default
        api_url = KYTOS_API+'/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        self.assertFalse(data['switches'][sw1]['enabled'])
        self.assertFalse(data['switches'][sw2]['enabled'])
        self.assertFalse(data['switches'][sw3]['enabled'])

        # enable the switches
        api_url = KYTOS_API+'/topology/v3/switches/%s/enable' % (sw1)
        response = requests.post(api_url)
        self.assertEqual(response.status_code, 201)
        api_url = KYTOS_API+'/topology/v3/switches/%s/enable' % (sw2)
        response = requests.post(api_url)
        self.assertEqual(response.status_code, 201)
        api_url = KYTOS_API+'/topology/v3/switches/%s/enable' % (sw3)
        response = requests.post(api_url)
        self.assertEqual(response.status_code, 201)

        # check if the switches are now enabled
        api_url = KYTOS_API+'/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        self.assertTrue(data['switches'][sw1]['enabled'])
        self.assertTrue(data['switches'][sw2]['enabled'])
        self.assertTrue(data['switches'][sw3]['enabled'])

        # restart kytos and check if the switches are still enabled
        self.net.start_controller(clean_config=False)
        self.net.wait_switches_connect()

        ## restore the status
        #api_url = KYTOS_API+'/topology/v3/restore'
        #response = requests.get(api_url)
        #self.assertEqual(response.status_code, 200)

        # check if the switches are still enabled and now with the links
        api_url = KYTOS_API+'/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        self.assertTrue(data['switches'][sw1]['enabled'])
        self.assertTrue(data['switches'][sw2]['enabled'])
        self.assertTrue(data['switches'][sw3]['enabled'])

    def test_030_disabling_switch_persistent(self):
        # TODO: 1) start kytosd -E; 2) disable a switch; 3) restart
        # kytos - kill kytos.pid && kytosd -E; 4) check if the switch
        # remain disabled
        self.assertTrue(True)

    def test_040_enabling_interface_persistent(self):
        sw1if1 = '00:00:00:00:00:00:00:01:1'
        sw2if1 = '00:00:00:00:00:00:00:02:1'

        # make sure the interfaces are disabled by default
        api_url = KYTOS_API+'/topology/v3/interfaces'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['interfaces']), 13)
        self.assertFalse(data['interfaces'][sw1if1]['enabled'])
        self.assertFalse(data['interfaces'][sw2if1]['enabled'])

        # enable the interfaces
        api_url = KYTOS_API+'/topology/v3/interfaces/%s/enable' % (sw1if1)
        response = requests.post(api_url)
        self.assertEqual(response.status_code, 200)
        api_url = KYTOS_API+'/topology/v3/interfaces/%s/enable' % (sw2if1)
        response = requests.post(api_url)
        self.assertEqual(response.status_code, 200)

        # check if the interfaces are now enabled
        api_url = KYTOS_API+'/topology/v3/interfaces'
        response = requests.get(api_url)
        data = response.json()
        self.assertTrue(data['interfaces'][sw1if1]['enabled'])
        self.assertTrue(data['interfaces'][sw2if1]['enabled'])

        # restart kytos and check if the interfaces are still enabled
        self.net.start_controller(clean_config=False)
        self.net.wait_switches_connect()
        time.sleep(5)

        ## restore the status
        #api_url = KYTOS_API+'/topology/v3/restore'
        #response = requests.get(api_url)
        #self.assertEqual(response.status_code, 200)

        # check if the interfaces are still enabled and now with the links
        api_url = KYTOS_API+'/topology/v3/interfaces'
        response = requests.get(api_url)
        data = response.json()
        self.assertTrue(data['interfaces'][sw1if1]['enabled'])
        self.assertTrue(data['interfaces'][sw2if1]['enabled'])

    def test_050_enabling_all_interfaces_persistent(self):
        # TODO: 1) start kytosd -E; 2) enable all interfaces; 3) restart
        # kytos - kill kytos.pid && kytosd -E; 4 check if all interfaces 
        # remain enabled
        #
        # Example: curl -s -X POST http://172.19.0.2:8181/api/kytos/topology/v3/interfaces/switch/00:00:00:00:00:00:00:01/enable
        self.assertTrue(True)

    def test_060_disabling_interface_persistent(self):
        # TODO: 1) start kytosd -E; 2) disable a interface; 3) restart
        # kytos - kill kytos.pid && kytosd -E; 4 check if the interface 
        # remain disabled
        self.assertTrue(True)

    def test_070_disabling_all_interfaces_persistent(self):
        # TODO: 1) start kytosd -E; 2) disable all interfaces; 3) restart
        # kytos - kill kytos.pid && kytosd -E; 4 check if all interfaces 
        # remain disabled
        self.assertTrue(True)

    def test_080_enabling_link_persistent(self):
        endpoint_a = '00:00:00:00:00:00:00:01:3'
        endpoint_b = '00:00:00:00:00:00:00:02:2'

        # make sure the links are disabled by default
        api_url = KYTOS_API+'/topology/v3/links'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['links']), 0)

        # enable the links (need to enable the switches and ports first)
        for i in [1, 2, 3]:
            sw = "00:00:00:00:00:00:00:0%d" % (i)
            api_url = KYTOS_API+'/topology/v3/switches/%s/enable' % (sw)
            response = requests.post(api_url)
            self.assertEqual(response.status_code, 201)
            api_url = KYTOS_API+'/topology/v3/interfaces/switch/%s/enable' % (sw)
            response = requests.post(api_url)
            self.assertEqual(response.status_code, 200)

        # wait 10s to kytos execute LLDP
        time.sleep(20)

        # now all the links should stay disabled
        api_url = KYTOS_API+'/topology/v3/links'
        response = requests.get(api_url)
        data = response.json()
        self.assertEqual(len(data['links']), 3)

        link_id1 = None
        for k,v in data['links'].items():
            link_a, link_b = v['endpoint_a']['id'], v['endpoint_b']['id']
            if set([link_a, link_b]) == set([endpoint_a, endpoint_b]):
                link_id1 = k
        self.assertNotEqual(link_id1, None)
        self.assertFalse(data['links'][link_id1]['enabled'])

        api_url = KYTOS_API+'/topology/v3/links/%s/enable' % (link_id1)
        response = requests.post(api_url)
        self.assertEqual(response.status_code, 201)

        # check if the links are now enabled
        api_url = KYTOS_API+'/topology/v3/links'
        response = requests.get(api_url)
        data = response.json()
        self.assertTrue(data['links'][link_id1]['enabled'])

        # restart kytos and check if the links are still enabled
        self.net.start_controller(clean_config=False)
        self.net.wait_switches_connect()

        ## restore the status
        #api_url = KYTOS_API+'/topology/v3/restore'
        #response = requests.get(api_url)
        #self.assertEqual(response.status_code, 200)

        # wait 10s to kytos execute LLDP
        time.sleep(10)

        # check if the links are still enabled and now with the links
        api_url = KYTOS_API+'/topology/v3/links'
        response = requests.get(api_url)
        data = response.json()
        self.assertTrue(data['links'][link_id1]['enabled'])

    def test_090_disabling_link_persistent(self):
        # TODO: 1) start kytosd -E; 2) disable the link1; 3) restart
        # kytos - kill kytos.pid && kytosd -E; 4 check if the link1
        # remain disabled
        self.assertTrue(True)

#    def test_100_all_enabled_should_activate_topology_discovery(self):
#        # /api/kytos/topology/v3/switches --> check if it is disabled
#        # /v3/switches/{dpid}/enable
#        # /api/kytos/topology/v3/switches --> check if it is enabled
#        # kill kytosd and restart, check if switches are still enabled
#        # check topology discovery

    def test_disabled_switch_on_start(self):

        sw = "00:00:00:00:00:00:00:01"

        # Start the controller setting an environment in
        # which all elements are disabled in a clean setting
        self.net.start_controller(clean_config=True, enable_all=False)
        self.net.wait_switches_connect()

        # Make sure the switch is disabled
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()

        assert response.status_code == 200
        assert data['switches'][sw]['enabled'] is False

    def test_disabling_switch(self):

        sw = "00:00:00:00:00:00:00:01"

        # Start the controller setting an environment in
        # which all elements are disabled in a clean setting
        self.net.start_controller(clean_config=True, enable_all=False)
        self.net.wait_switches_connect()

        # Enable the switch
        api_url = KYTOS_API + '/topology/v3/switches/%s/enable' % sw
        response = requests.post(api_url)
        assert response.status_code == 201

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Check if the switch is enabled
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()

        assert response.status_code == 200
        assert data['switches'][sw]['enabled'] is True

        # Disable the switch and check if the switch is disabled
        api_url = KYTOS_API + '/topology/v3/switches/%s/disable' % sw
        print(api_url)
        response = requests.post(api_url)
        assert response.status_code == 201

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        assert data['switches'][sw]['enabled'] is False

    def test_remove_switch_metadata(self):

        sw = "00:00:00:00:00:00:00:01"

        # Start the controller setting an environment in
        # which all elements are disabled in a clean setting
        self.net.start_controller(clean_config=True, enable_all=False)
        self.net.wait_switches_connect()

        # Insert switch metadata
        payload = {"tmp_key": "tmp_value"}
        api_url = KYTOS_API + '/topology/v3/switches/%s/metadata' % sw
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Verify that the metadata is inserted
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        assert payload.keys()[0] in data['switches'][sw]['metadata'].keys()

        # Delete the switch metadata
        api_url = KYTOS_API + '/topology/v3/switches/%s/metadata/%s' % (sw, payload.keys()[0])
        response = requests.delete(api_url)
        assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Make sure the metadata is removed
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        assert payload.keys()[0] not in data['switches'][sw]['metadata'].keys()

    def test_remove_interfaces_metadata(self):

        intf = "00:00:00:00:00:00:00:01:4"

        # Start the controller setting an environment in
        # which all elements are disabled in a clean setting
        self.net.start_controller(clean_config=True, enable_all=False)
        self.net.wait_switches_connect()

        # Insert interface metadata
        payload = {"tmp_key": "tmp_value"}
        api_url = KYTOS_API + '/topology/v3/interfaces/%s/metadata' % intf
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Verify that the metadata is inserted
        api_url = KYTOS_API + '/topology/v3/interfaces/%s/metadata' % intf
        response = requests.get(api_url)
        data = response.json()
        assert payload.keys()[0] in data['metadata'].keys()

        # Delete the interface metadata
        api_url = KYTOS_API + '/topology/v3/interfaces/%s/metadata/%s' % (intf, payload.keys()[0])
        response = requests.delete(api_url)
        assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Make sure the metadata is removed
        api_url = KYTOS_API + '/topology/v3/interfaces/%s/metadata' % intf
        response = requests.get(api_url)
        data = response.json()
        assert payload.keys()[0] not in data['metadata'].keys()

    def test_remove_links_metadata(self):
        pass
