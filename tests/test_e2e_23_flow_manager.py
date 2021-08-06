import json
import time

import pytest
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

    @pytest.mark.xfail
    @pytest.mark.parametrize('execution_number', range(10))
    def test_005_install_flow(self, execution_number):
        """
        Tests the inclusion of a flow with matches fields and
        without actions after the creation of a set of flows
        :param execution_number: Times the test will run
        """

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 10,
                    "match": {
                        "in_port": 2,
                        "dl_vlan": 200
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 3
                        }
                    ]
                },
                {
                    "priority": 10,
                    "match": {
                        "in_port": 3,
                        "dl_vlan": 300
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 4
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 202
        data = response.json()
        assert 'FlowMod Messages Sent' in data['response']

        # wait for the flow to be installed
        time.sleep(10)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 4
        assert 'actions=output:"s1-eth2"' in flows_s1

        payload2 = {
            "flows": [
                {
                    "priority": 10,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    }
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload2), headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(10)

        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 4

        assert 'actions=output:"s1-eth3"' in flows_s1
        assert 'actions=output:"s1-eth4"' in flows_s1
        assert 'actions=output:"s1-eth2"' not in flows_s1

        assert 'actions=drop' in flows_s1

    def test_010_install_flow(self):
        """Tests the inclusion of multiple flows with
        the same priority and different and different
        matches and actions on the same payload"""

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 10,
                    "match": {
                        "in_port": 2,
                        "dl_vlan": 200
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 3
                        }
                    ]
                },
                {
                    "priority": 10,
                    "match": {
                        "in_port": 3,
                        "dl_vlan": 300
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 4
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 202
        data = response.json()
        assert 'FlowMod Messages Sent' in data['response']

        # wait for the flow to be installed
        time.sleep(10)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 4
        assert 'actions=output:"s1-eth2"' in flows_s1

        payload2 = {
            "flows": [
                {
                    "priority": 10,
                    "match": {
                        "in_port": 1
                    }
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload2), headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(10)

        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 5

        assert 'actions=output:"s1-eth2"' in flows_s1
        assert 'actions=output:"s1-eth3"' in flows_s1
        assert 'actions=output:"s1-eth4"' in flows_s1
        assert 'actions=drop' in flows_s1

    @pytest.mark.parametrize('execution_number', range(10))
    def test_015_install_flow(self, execution_number):
        """
        Tests the inclusion of a flow without match fields and
        with one action after the creation of a set of flows
        :param execution_number: Times the test will run
        """
        payload = {
            "flows": [
                {
                    "priority": 10,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 10,
                    "match": {
                        "in_port": 2,
                        "dl_vlan": 200
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 3
                        }
                    ]
                },
                {
                    "priority": 10,
                    "match": {
                        "in_port": 3,
                        "dl_vlan": 300
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 4
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 202
        data = response.json()
        assert 'FlowMod Messages Sent' in data['response']

        # wait for the flow to be installed
        time.sleep(10)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 4
        assert 'actions=output:"s1-eth2"' in flows_s1

        payload2 = {
            "flows": [
                {
                    "priority": 10,
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 5
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload2), headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(10)

        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 5

        assert 'actions=output:"s1-eth2"' in flows_s1
        assert 'actions=output:"s1-eth3"' in flows_s1
        assert 'actions=output:"s1-eth4"' in flows_s1

        assert 'actions=output:5' in flows_s1

    def test_020_install_flow(self):
        """
        Tests the addition of multiple flows with the same cookie_id
        and different matches and actions on the same payload
        """

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 10,
                    "match": {
                        "in_port": 2,
                        "dl_vlan": 200
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 3
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(15)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 3
        assert 'actions=output:"s1-eth2"' in flows_s1

        payload2 = {
            "flows": [
                {
                    "priority": 10,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 3,
                        "dl_vlan": 300
                    },
                    "actions": [
                        {
                            "action_type": "set_vlan",
                            "vlan_id": 400
                        },
                        {
                            "action_type": "output",
                            "port": 1
                        }
                    ]
                },
                {
                    "priority": 10,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 4
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 1
                        }
                    ]
                },

            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload2), headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(15)

        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 5

        assert 'actions=output:"s1-eth2"' in flows_s1
        assert 'actions=output:"s1-eth3"' in flows_s1
        assert 'in_port="s1-eth3"' in flows_s1
        assert 'actions=mod_vlan_vid:400,output:"s1-eth1"' in flows_s1
        assert 'in_port="s1-eth4"' in flows_s1
        assert 'actions=output:"s1-eth1"' in flows_s1

    def test_025_install_flow(self):
        """
        Tests the addition of multiple flows with the same cookie_id
        and different matches and actions on different payloads
        """

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 10,
                    "match": {
                        "in_port": 2,
                        "dl_vlan": 200
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 3
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(15)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 3
        assert 'actions=output:"s1-eth2"' in flows_s1
        assert 'actions=output:"s1-eth3"' in flows_s1

        payload2 = {
            "flows": [
                {
                    "priority": 10,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 3,
                        "dl_vlan": 300
                    },
                    "actions": [
                        {
                            "action_type": "set_vlan",
                            "vlan_id": 400
                        },
                        {
                            "action_type": "output",
                            "port": 1
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload2),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(15)

        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 4
        assert 'actions=output:"s1-eth2"' in flows_s1
        assert 'actions=output:"s1-eth3"' in flows_s1
        assert 'in_port="s1-eth3"' in flows_s1
        assert 'actions=mod_vlan_vid:400,output:"s1-eth1"' in flows_s1

        payload3 = {
            "flows": [
                {
                    "priority": 10,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 4
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 1
                        }
                    ]
                },

            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload3), headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(15)

        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 5

        assert 'in_port="s1-eth4"' in flows_s1
        assert 'actions=output:"s1-eth1"' in flows_s1

    def test_030_install_flow(self):
        """
        Tests the addition of multiple flows with the
        same matches and actions on the same payload
        """

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 10,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 10,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 10,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
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
        time.sleep(15)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=output:"s1-eth2"' in flows_s1

    def test_035_install_flow(self):
        """
        Tests the addition of multiple flows with the
        same matches and actions on different payloads
        """

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
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
        time.sleep(15)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=output:"s1-eth2"' in flows_s1

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(15)

        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=output:"s1-eth2"' in flows_s1

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(15)

        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=output:"s1-eth2"' in flows_s1

    def test_040_install_flow(self):
        """
        Tests the addition of multiple flows with the
        same cookie_id, matches and actions on the same payload
        """

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 10,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 10,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 10,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
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
        time.sleep(15)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=output:"s1-eth2"' in flows_s1

    def test_045_install_flow(self):
        """
        Tests the addition of multiple flows with the same
        cookie_id, matches and actions on different payloads
        """

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
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
        time.sleep(15)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=output:"s1-eth2"' in flows_s1

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(15)

        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=output:"s1-eth2"' in flows_s1

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(15)

        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=output:"s1-eth2"' in flows_s1

    def test_050_install_flow(self):
        """
        Tests the creation of multiple flows with different priorities
        and the same cookie_id, matches, and actions on the same payload
        """

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 20,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
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
        time.sleep(15)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 3
        assert 'actions=output:"s1-eth2"' in flows_s1

    def test_055_install_flow(self):
        """
        Tests the creation of multiple flows with different priorities
        and the same cookie_id, matches, and actions on different payloads
        """

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
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
        time.sleep(15)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 2
        assert 'actions=output:"s1-eth2"' in flows_s1

        payload1 = {
            "flows": [
                {
                    "priority": 20,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
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
        requests.post(api_url, data=json.dumps(payload1),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(15)

        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 3
        assert 'actions=output:"s1-eth2"' in flows_s1

    def test_060_install_flow(self):
        """
        Tests the inclusion of a flow without matches and actions
        after being created some flows with different priorities and
        the same cookie_id, matches, and actions on a different payload
        """

        payload = {
            "flows": [
                {
                    "priority": 10,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 1,
                        "dl_vlan": 100
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 2
                        }
                    ]
                },
                {
                    "priority": 20,
                    "cookie": 84114904,
                    "match": {
                        "in_port": 2,
                        "dl_vlan": 200
                    },
                    "actions": [
                        {
                            "action_type": "output",
                            "port": 3
                        }
                    ]
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(15)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 3
        assert 'actions=output:"s1-eth2"' in flows_s1
        assert 'actions=output:"s1-eth3"' in flows_s1

        payload1 = {
            "flows": [
                {
                    "priority": 25,
                }
            ]
        }

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        requests.post(api_url, data=json.dumps(payload1),
                      headers={'Content-type': 'application/json'})

        # wait for the flow to be installed
        time.sleep(15)

        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 4
        assert 'actions=drop' in flows_s1

    def test_065_install_flow(self):
        """
        Tests the performance and race condition
        with the creation of multiple flows
        """
        import subprocess

        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'

        import shlex
        for i in range(100, 200):
            cmd = '''curl -X POST -H 'Content-type: application/json' ''' + api_url + '''
                    -d "{\\"flows\\": [{\\"priority\\": 100, \\"cookie\\": 84114904,
                    \\"match\\": {\\"in_port\\": 1, \\"dl_vlan\\":''' + str(i) + '''},
                    \\"actions\\": [{\\"action_type\\": \\"output\\", \\"port\\": 2}]}]}"'''

            args = shlex.split(cmd)
            process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # wait for the flow to be installed
        time.sleep(10)

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')

        assert len(flows_s1.split('\r\n ')) == 101

    def create_flow(self, vlan_id):
        payload = {
            "flows": [{
                "priority": 10,
                "match": {
                    "in_port": 1,
                    "dl_vlan": vlan_id
                },
                "actions": [{
                    "action_type": "output",
                    "port": 2
                }]
            }]
        }
        api_url = KYTOS_API + '/flow_manager/v2/flows/00:00:00:00:00:00:00:01'
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers = {'Content-type': 'application/json'})

        assert response.status_code == 202
        data = response.json()
        assert 'FlowMod Messages Sent' in data['response']

    @pytest.mark.xfail
    def test_070_install_flow(self):
        """
        Tests the performance and race condition with
        the creation of multiple flows using threading
        """
        import threading
        threads = list()
        for vlan_id in range(100, 200):
            t = threading.Thread(target=self.create_flow, args=(vlan_id,))
            threads.append(t)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        s1 = self.net.net.get('s1')
        flows_s1 = s1.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 101
