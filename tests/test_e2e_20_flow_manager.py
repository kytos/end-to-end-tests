import json
import pytest
import unittest
import requests
from tests.helpers import NetworkTest
import os
import time

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % (CONTROLLER)

class TestE2EFlowManager:
    net = None

    @classmethod
    def setup_class(cls):
        cls.net = NetworkTest(CONTROLLER)
        cls.net.start()
        cls.net.wait_switches_connect()

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def test_020_install_flow(self):
        """Test if, after kytos restart, a flow installed to a switch will
           still be installed."""
        self.net.restart_kytos_clean()
        time.sleep(5)

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
        time.sleep(20)

        # restart controller keeping configuration
        self.net.start_controller(del_flows=True)
        # maybe stop the controller, remove the flow from the switch and then restart

        time.sleep(20)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=output:"s1-eth2"' in flows_s1

    def test_020_install_flows(self):
        """Test if, after kytos restart, a flow installed to all switches will
           still be installed."""
        self.net.restart_kytos_clean()
        time.sleep(5)

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
        time.sleep(20)

        # restart controller keeping configuration
        self.net.start_controller(del_flows=True)
        # maybe stop the controller, remove the flow from the switch and then restart

        time.sleep(20)

        for sw_name in ['s1', 's2', 's3']:
            sw = self.net.net.get(sw_name)
            flows_sw = sw.dpctl('dump-flows')
            assert len(flows_sw.split('\r\n ')) == 2
            assert 'actions=output:"%s-eth2"' % sw_name in flows_sw

    def test_020_delete_flow(self):
        """Test if, after kytos restart, a flow deleted from a switch will
           still be deleted."""
        self.net.restart_kytos_clean()
        time.sleep(5)

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
        time.sleep(20)

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.delete(api_url, data=json.dumps(payload), 
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'FlowMod Messages Sent' in data['response']

        # wait for the flow to be deleted
        time.sleep(20)

        # restart controller keeping configuration
        self.net.start_controller(del_flows=True)
        # maybe stop the controller, remove the flow from the switch and then restart

        time.sleep(20)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 1
        assert 'actions=output:"s1-eth2"' not in flows_s1

    def test_020_delete_flows(self):
        """Test if, after kytos restart, a flow deleted from all switches will
           still be deleted."""
        self.net.restart_kytos_clean()
        time.sleep(5)

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
        time.sleep(20)

        # delete the flow
        api_url = KYTOS_API + '/flow_manager/v2/flows'
        response = requests.delete(api_url, data=json.dumps(payload), 
                                   headers={'Content-type': 'application/json'})
        assert response.status_code == 200
        data = response.json()
        assert 'FlowMod Messages Sent' in data['response']

        # wait for the flow to be deleted
        time.sleep(20)

        # restart controller keeping configuration
        self.net.start_controller(del_flows=True)
        # maybe stop the controller, remove the flow from the switch and then restart

        time.sleep(20)

        for sw_name in ['s1', 's2', 's3']:
            sw = self.net.net.get(sw_name)
            flows_sw = sw.dpctl('dump-flows')
            assert len(flows_sw.split('\r\n ')) == 1
            assert 'actions=output:"%s-eth2"' % sw_name not in flows_sw
