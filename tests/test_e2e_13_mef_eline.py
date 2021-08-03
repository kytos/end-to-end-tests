import json
import time
from datetime import datetime

import pytest
import requests

from tests.helpers import NetworkTest

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % CONTROLLER

TIME_FMT = "%Y-%m-%dT%H:%M:%S+0000"


class TestE2EMefEline:
    net = None
    evcs = {}

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
        cls.net.restart_kytos_clean()
        cls.net.wait_switches_connect()
        time.sleep(5)

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def create_evc(self, vlan_id, store=False):
        payload = {
            "name": "Vlan_%s" % vlan_id,
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": vlan_id}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": vlan_id}
            }
        }
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        data = response.json()
        if store:
            self.evcs[vlan_id] = data['circuit_id']
        return data['circuit_id']

    def test_005_patch_unknown_circuit(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        primary_path = data['primary_path']

        payload = {
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:3"}}
            ]
        }

        # It sets a new circuit's primary_path
        response = requests.patch(api_url + evc1 + "A", data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 404

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data2 = response.json()
        assert data == data2

    def test_010_patch_an_empty_uni_a(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_a": {}
        }

        # It tries to setting up a new uni_a
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_015_patch_an_inconsistent_uni_a(self):
        """ No existing switch """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:99:1"
            }
        }

        # It tries to setting up a new uni_a
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_020_patch_an_inconsistent_uni_a(self):
        """ Valid switch but invalid Interface ID """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:99"
            }
        }

        # It tries to setting up a new uni_a
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_025_patch_an_inconsistent_uni_a(self):
        """ Valid switch, valid Interface ID, but invalid tag_type (string) """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": "A",
                    "value": 101
                }
            }
        }

        # It tries to setting up a new uni_a
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_030_patch_an_inconsistent_uni_a(self):
        """ Valid switch, valid Interface ID, but invalid tag_type (invalid value) """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 2,
                    "value": 101
                }
            }
        }

        # It tries to setting up a new uni_a
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_035_patch_an_inconsistent_uni_a(self):
        """ Valid switch, valid Interface ID, valid tag_type, but invalid tag """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 1,
                    "value": -1
                }
            }
        }

        # It tries to setting up a new uni_a
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_040_patch_an_inconsistent_uni_a(self):
        """ Valid switch, valid Interface ID, valid tag_type, but invalid tag """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 1,
                    "value": "bla"
                }
            }
        }

        # It tries to setting up a new uni_a
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_045_patch_an_inconsistent_uni_a(self):
        """ Valid switch, valid Interface ID, valid tag_type, but invalid tag """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 1,
                    "value": 99999
                }
            }
        }

        # It tries to setting up a new uni_a
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_050_patch_an_inconsistent_uni_a(self):
        """ Valid switch, valid Interface ID, valid tag_type, but invalid tag_name """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type_one": 1,
                    "value": 101
                }
            }
        }

        # It tries to setting up a new uni_a
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    # TODO
    """ This test should change the Vlan range and modify it to a plan value outside that range """
    def test_055_patch_an_inconsistent_uni_a(self):
        pass

    def test_060_patch_an_empty_uni_z(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_z": {}
        }

        # It tries to setting up a new uni_z
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_065_patch_an_inconsistent_uni_z(self):
        """ No existing switch """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:04:1"
            }
        }

        # It tries to setting up a new uni_z
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_070_patch_an_inconsistent_uni_z(self):
        """ Valid switch but invalid Interface ID """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:01:99"
            }
        }

        # It tries to setting up a new uni_z
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_075_patch_an_inconsistent_uni_z(self):
        """ Valid switch, valid Interface ID, but invalid tag_type (string) """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": "A",
                    "value": 101
                }
            }
        }

        # It tries to setting up a new uni_z
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_080_patch_an_inconsistent_uni_z(self):
        """ Valid switch, valid Interface ID, but invalid tag_type (invalid value) """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 2,
                    "value": 101
                }
            }
        }

        # It tries to setting up a new uni_z
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_085_patch_an_inconsistent_uni_z(self):
        """ Valid switch, valid Interface ID, valid tag_type, but invalid tag """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 1,
                    "value": -1
                }
            }
        }

        # It tries to setting up a new uni_z
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_090_patch_an_inconsistent_uni_z(self):
        """ Valid switch, valid Interface ID, valid tag_type, but invalid tag """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 1,
                    "value": "bla"
                }
            }
        }

        # It tries to setting up a new uni_z
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_095_patch_an_inconsistent_uni_z(self):
        """ Valid switch, valid Interface ID, valid tag_type, but invalid tag """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 1,
                    "value": 99999
                }
            }
        }

        # It tries to setting up a new uni_z
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_100_patch_an_inconsistent_uni_z(self):
        """ Valid switch, valid Interface ID, valid tag_type, but invalid tag_name """

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type_one": 1,
                    "value": 101
                }
            }
        }

        # It tries to setting up a new uni_z
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """It is returning Response [200], should be 400"""
    @pytest.mark.xfail
    def test_105_patch_an_inconsistent_primary_path(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            },
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}
            ]
        }
        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        payload2 = {
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:1"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:1"}}
            ]
        }

        # It sets a new circuit's primary_path
        response = requests.patch(api_url + evc1, data=json.dumps(payload2),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400
        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['primary_path'][0]['endpoint_a']['id'] == payload1['primary_path'][0]['endpoint_a']['id']
        assert data['primary_path'][0]['endpoint_b']['id'] == payload1['primary_path'][0]['endpoint_b']['id']
        assert data['active'] is True

    """It is returning Response [200], should be 400"""
    @pytest.mark.xfail
    def test_110_patch_an_unrelated_primary_path(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            },
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}
            ]
        }
        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        payload2 = {
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:3"}}
            ]
        }

        # It sets a new circuit's primary_path
        response = requests.patch(api_url + evc1, data=json.dumps(payload2),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400
        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['primary_path'][0]['endpoint_a']['id'] == payload1['primary_path'][0]['endpoint_a']['id']
        assert data['primary_path'][0]['endpoint_b']['id'] == payload1['primary_path'][0]['endpoint_b']['id']
        assert data['active'] is True

    """It is returning Response [200], should be 400"""
    @pytest.mark.xfail
    def test_115_patch_an_empty_primary_path(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": False,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            },
            "primary_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:3"}}
            ]
        }
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        payload = {
            "primary_path": []
        }

        # It sets a new circuit's primary_path
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['primary_path'] != []
        assert data['active'] is True

    """It is returning Response [200], should be 400"""
    @pytest.mark.xfail
    def test_120_patch_an_inconsistent_backup_path(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            },
            "backup_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}
            ]
        }
        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        payload2 = {
            "backup_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:1"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:1"}}
            ]
        }

        # It sets a new circuit's primary_path
        response = requests.patch(api_url + evc1, data=json.dumps(payload2),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400
        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['backup_path'][0]['endpoint_a']['id'] == payload1['backup_path'][0]['endpoint_a']['id']
        assert data['backup_path'][0]['endpoint_b']['id'] == payload1['backup_path'][0]['endpoint_b']['id']
        assert data['active'] is True

    """It is returning Response [200], should be 400"""
    @pytest.mark.xfail
    def test_125_patch_an_unrelated_backup_path(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            },
            "backup_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}
            ]
        }
        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        payload2 = {
            "backup_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:3"}}
            ]
        }

        # It sets a new circuit's primary_path
        response = requests.patch(api_url + evc1, data=json.dumps(payload2),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400
        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['backup_path'][0]['endpoint_a']['id'] == payload1['backup_path'][0]['endpoint_a']['id']
        assert data['backup_path'][0]['endpoint_b']['id'] == payload1['backup_path'][0]['endpoint_b']['id']
        assert data['active'] is True

    """It is returning Response [500], should be 400"""
    @pytest.mark.xfail
    def test_130_patch_an_inconsistent_primary_links(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            },
            "primary_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}
            ]
        }
        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        payload2 = {
            "primary_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:1"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:1"}}
            ]
        }

        # It sets a new circuit's primary_path
        response = requests.patch(api_url + evc1, data=json.dumps(payload2),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400
        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['primary_links'][0]['endpoint_a']['id'] == payload1['primary_links'][0]['endpoint_a']['id']
        assert data['primary_links'][0]['endpoint_b']['id'] == payload1['primary_links'][0]['endpoint_b']['id']
        assert data['active'] is True

    """It is returning Response [500], should be 400"""
    @pytest.mark.xfail
    def test_135_patch_an_unrelated_primary_links(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            },
            "primary_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}
            ]
        }
        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        payload2 = {
            "primary_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:3"}}
            ]
        }

        # It sets a new circuit's primary_path
        response = requests.patch(api_url + evc1, data=json.dumps(payload2),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400
        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['primary_links'][0]['endpoint_a']['id'] == payload1['primary_links'][0]['endpoint_a']['id']
        assert data['primary_links'][0]['endpoint_b']['id'] == payload1['primary_links'][0]['endpoint_b']['id']
        assert data['active'] is True

    """It is returning Response [500], should be 400"""
    @pytest.mark.xfail
    def test_140_patch_an_inconsistent_backup_links(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            },
            "primary_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:3"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:03:2"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:3"}}
            ],
            "backup_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}
            ]
        }
        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        payload2 = {
            "backup_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:1"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:1"}}
            ]
        }

        # It sets a new circuit's primary_path
        response = requests.patch(api_url + evc1, data=json.dumps(payload2),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400
        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['backup_links'][0]['endpoint_a']['id'] == payload1['backup_links'][0]['endpoint_a']['id']
        assert data['backup_links'][0]['endpoint_b']['id'] == payload1['backup_links'][0]['endpoint_b']['id']
        assert data['active'] is True

    """It is returning Response [500], should be 400"""
    @pytest.mark.xfail
    def test_145_patch_an_unrelated_backup_links(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            },
            "primary_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:3"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:03:2"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:3"}}
            ],
            "backup_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}}
            ]
        }
        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        payload2 = {
            "backup_links": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:4"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:3"}}
            ]
        }

        # It sets a new circuit's primary_path
        response = requests.patch(api_url + evc1, data=json.dumps(payload2),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['backup_links'][0]['endpoint_a']['id'] == payload1['backup_links'][0]['endpoint_a']['id']
        assert data['backup_links'][0]['endpoint_b']['id'] == payload1['backup_links'][0]['endpoint_b']['id']
        assert data['active'] is True

    """It is returning Response 500, but it should return a failure code"""
    @pytest.mark.xfail
    def test_150_patch_creation_time(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        creation_time = data['creation_time']

        start = datetime.now()
        payload = {
            "creation_time": start.strftime(TIME_FMT)
        }

        # It sets a new circuit's creation_time
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

        time.sleep(10)

        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['creation_time'] == creation_time

    def test_155_patch_evc_active(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        payload = {
            "active": False,
        }

        # It sets a new circuit's creation_time
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['active'] is True

    """It is returning Response 200, should be 400"""
    @pytest.mark.xfail
    def test_160_patch_request_time(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        start = datetime.now()
        payload = {
            "request_time": start.strftime(TIME_FMT)
        }

        # It sets a new circuit's creation_time
        response = requests.patch(api_url + evc1, data=json.dumps(payload),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['request_time'] != start.strftime(TIME_FMT)

    """It is returning Response 500, but it should return a failure code"""
    @pytest.mark.xfail
    def test_165_patch_current_path(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            }
        }

        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        data = response.json()
        evc1 = data['circuit_id']

        time.sleep(10)

        payload2 = {
            "current_path": [{
                "enabled": False
            }]
        }

        # It sets a new circuit's creation_time
        response = requests.patch(api_url + evc1, data=json.dumps(payload2),
                                  headers={'Content-type': 'application/json'})
        assert response.status_code == 400

        time.sleep(10)

        # It verifies EVC's current_path
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data["current_path"]['enabled'] is True

    def test_170_post_invalid_json(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload = {
            "unknown_tag": "my evc1",
        }
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})

        assert response.status_code == 400

    def test_175_post_empty_json(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload = {}
        response = requests.post(api_url, data=json.dumps(payload),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_180_post_unknown_port_on_interface(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:9999",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            }
        }

        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_185_post_unknown_interface(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:09:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            }
        }

        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_190_post_an_evc_twice(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        payload1 = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1"
            }
        }

        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 201

        response = requests.post(api_url, data=json.dumps(payload1),
                                 headers={'Content-type': 'application/json'})
        assert response.status_code == 409

    def test_195_get_unknown_circuit(self):
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(100)

        # It verifies EVC's data
        response = requests.get(api_url + evc1 + "A")
        assert response.status_code == 404

    """It is returning Response 500, should be 400"""
    @pytest.mark.xfail
    def test_200_post_on_dynamic_backup_path_and_backup_path(self):
        payload = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            "backup_path": [
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:3"}}
            ]
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """It is returning Response 201, should be 400"""
    @pytest.mark.xfail
    def test_205_post_on_false_dynamic_backup_path_and_empty_primary_path(self):
        payload = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": False,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            'primary_path': []
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """It is returning Response 201, should be 400"""
    @pytest.mark.xfail
    def test_210_post_on_false_dynamic_backup_path_and_none_primary_path(self):
        payload = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": False,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 100}
            }
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """It is returning Response 201, should be 400"""
    @pytest.mark.xfail
    def test_215_post_on_none_dynamic_backup_path_and_empty_primary_path(self):
        payload = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            'primary_path': []
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """It is returning Response 201, should be 400"""
    @pytest.mark.xfail
    def test_220_post_on_none_dynamic_backup_path_and_none_primary_path(self):
        payload = {
            "name": "my evc1",
            "enabled": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {"tag_type": 1, "value": 100}
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:02:1",
                "tag": {"tag_type": 1, "value": 100}
            }
        }

        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    # TODO tests over primary_links and backup_links
