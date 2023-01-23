import requests
from tests.helpers import NetworkTest
import time
import pytest

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api' % CONTROLLER


class TestE2ESDNTrace:
    net = None
    circuit = None

    @classmethod
    def setup_class(cls):
        cls.net = NetworkTest(CONTROLLER, topo_name='linear10')
        cls.net.start()
        cls.net.restart_kytos_clean()
        cls.net.wait_switches_connect()
        time.sleep(10)
        circuit_id = cls.create_evc(400)
        time.sleep(10)
        cls.circuit = cls.get_evc(circuit_id)

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    @staticmethod
    def create_evc(vlan_id, interface_a="00:00:00:00:00:00:00:01:1", interface_z="00:00:00:00:00:00:00:0a:1"):
        payload = {
            "name": "Vlan_%s" % vlan_id,
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": interface_a,
                "tag": {"tag_type": 1, "value": vlan_id}
            },
            "uni_z": {
                "interface_id": interface_z,
                "tag": {"tag_type": 1, "value": vlan_id}
            }
        }
        api_url = KYTOS_API + '/kytos/mef_eline/v2/evc/'
        response = requests.post(api_url, json=payload)
        assert response.status_code == 201, response.text
        data = response.json()
        return data['circuit_id']

    @staticmethod
    def get_evc(circuit_id):
        api_url = KYTOS_API + '/kytos/mef_eline/v2/evc/'
        response = requests.get(api_url+circuit_id)
        assert response.status_code == 200, response.text
        data = response.json()
        return data

    def test_001_run_sdntrace_cp(self):
        """Run SDNTrace-CP (Control Plane)."""
        # Trace from UNI_A
        payload = {
            "trace": {
                "switch": {"dpid": "00:00:00:00:00:00:00:01", "in_port": 1},
                "eth": {"dl_type": 33024, "dl_vlan": 400}
            }
        }
        api_url = KYTOS_API + '/amlight/sdntrace_cp/trace'
        response = requests.put(api_url, json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert "result" in data, data
        assert len(data["result"]) == 10, data

        expected = [
            (
                l['endpoint_b']['switch'],
                l['endpoint_b']['port_number'],
                l['metadata']['s_vlan']['value']
            )
            for l in self.circuit['current_path']
        ]
        expected.insert(0, ('00:00:00:00:00:00:00:01', 1, 400))

        actual = [
            (step['dpid'], step['port'], step['vlan'])
            for step in data["result"]
        ]

        assert expected == actual, f"Expected {expected}. Actual: {actual}"

        # Trace from UNI_Z
        payload = {
            "trace": {
                "switch": {"dpid": "00:00:00:00:00:00:00:0a", "in_port": 1},
                "eth": {"dl_type": 33024, "dl_vlan": 400}
            }
        }
        api_url = KYTOS_API + '/amlight/sdntrace_cp/trace'
        response = requests.put(api_url, json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert "result" in data
        assert len(data["result"]) == 10, data

        expected = [
            (
                l['endpoint_a']['switch'],
                l['endpoint_a']['port_number'],
                l['metadata']['s_vlan']['value']
            )
            for l in reversed(self.circuit['current_path'])
        ]
        expected.insert(0, ('00:00:00:00:00:00:00:0a', 1, 400))

        actual = [
            (step['dpid'], step['port'], step['vlan'])
            for step in data["result"]
        ]

        assert expected == actual, f"Expected {expected}. Actual: {actual}"

    def wait_sdntrace_result(self, trace_id, timeout=10):
        """Wait until sdntrace finishes."""
        wait_count = 0
        while wait_count < timeout:
            try:
                api_url = KYTOS_API + '/amlight/sdntrace/trace'
                response = requests.get(f"{api_url}/{trace_id}")
                data = response.json()
                assert data["result"][-1]["reason"] == "done"
                break
            except:
                time.sleep(1)
                wait_count += 1
        else:
            msg = 'Timeout while waiting from sdntrace result.'
            raise Exception(msg)
        return data["result"]

    def test_010_run_sdntrace(self):
        """Run SDNTrace (Data Plane trace)."""
        # Trace from UNI_A
        payload = {
            "trace": {
                "switch": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 1
                },
                "eth": {
                    "dl_vlan": 400,
                    "dl_vlan_pcp": 4,
                    "dl_type": 2048
                },
                "ip": {
                    "nw_src": "0.0.0.1",
                    "nw_dst": "0.0.0.2",
                    "nw_tos": 5,
                    "nw_proto": 17
                },
                "tp": {
                    "tp_src": 33948,
                    "tp_dst": 53
                }
            }
        }

        api_url = KYTOS_API + '/amlight/sdntrace/trace'
        response = requests.put(api_url, json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert "result" in data, data
        assert "trace_id" in data["result"], data
        result = self.wait_sdntrace_result(data["result"]["trace_id"])

        expected = [
            (
                l['endpoint_b']['switch'],
                l['endpoint_b']['port_number'],
            )
            for l in self.circuit['current_path']
        ]

        actual = [
            (step['dpid'], step['port']) for step in result[1:-1]
        ]

        assert expected == actual, f"Expected {expected}. Actual: {actual}"

        # Trace from UNI_Z
        payload = {
            "trace": {
                "switch": {
                    "dpid": "00:00:00:00:00:00:00:0a",
                    "in_port": 1
                },
                "eth": {
                    "dl_vlan": 400,
                    "dl_vlan_pcp": 4,
                    "dl_type": 2048
                },
                "ip": {
                    "nw_src": "0.0.0.1",
                    "nw_dst": "0.0.0.2",
                    "nw_tos": 5,
                    "nw_proto": 17
                },
                "tp": {
                    "tp_src": 33948,
                    "tp_dst": 53
                }
            }
        }

        api_url = KYTOS_API + '/amlight/sdntrace/trace'
        response = requests.put(api_url, json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert "result" in data, data
        assert "trace_id" in data["result"], data
        result = self.wait_sdntrace_result(data["result"]["trace_id"])

        expected = [
            (
                l['endpoint_a']['switch'],
                l['endpoint_a']['port_number'],
            )
            for l in reversed(self.circuit['current_path'])
        ]

        actual = [
            (step['dpid'], step['port']) for step in result[1:-1]
        ]

        assert expected == actual, f"Expected {expected}. Actual: {actual}"

    def test_020_run_sdntrace_fail_missing_flow(self):
        """Run SDNTrace-CP with a failure due to missing flows:
        - delete flow from intermediate switch
        - make sure sdntrace_cp detects the failure
        - make sure sdntrace detects the failure
        - redeploy evc and make sure sdntrace / sdntrace_cp works
        """
        # 1. delete flow
        delete_flow = {
            "flows": [
                {
                    'cookie': int("0xaa%s" % self.circuit['id'], 16),
                    'cookie_mask': 0xffffffffffffffff,
                }
            ]
        }

        api_url = KYTOS_API + '/kytos/flow_manager/v2/flows/00:00:00:00:00:00:00:05'
        response = requests.delete(api_url, json=delete_flow)
        assert response.status_code == 202, response.text
        time.sleep(10)

        # 2. sdntrace control plane - Trace from UNI_A
        payload_1 = {
            "trace": {
                "switch": {"dpid": "00:00:00:00:00:00:00:01", "in_port": 1},
                "eth": {"dl_type": 33024, "dl_vlan": 400}
            }
        }
        api_url = KYTOS_API + '/amlight/sdntrace_cp/trace'
        response = requests.put(api_url, json=payload_1)
        data = response.json()
        # only 4 steps are expected: starting, 1->2, 2->3, 3->4
        assert len(data["result"]) == 4, str(data)

        full_path = [
            (
                l['endpoint_b']['switch'],
                l['endpoint_b']['port_number'],
                l['metadata']['s_vlan']['value']
            )
            for l in self.circuit['current_path']
        ]

        actual = [
            (step['dpid'], step['port'], step['vlan'])
            for step in data["result"][1:]
        ]

        assert full_path != actual, f"Full path {full_path}. Actual: {actual}"
        assert full_path[:3] == actual, f"Expected {full_path[:3]}. Actual: {actual}"

        # 3. sdntrace data plane - Trace from UNI_A
        payload_2 = {
            "trace": {
                "switch": {
                    "dpid": "00:00:00:00:00:00:00:01",
                    "in_port": 1
                },
                "eth": {
                    "dl_vlan": 400,
                    "dl_vlan_pcp": 4,
                    "dl_type": 2048
                },
                "ip": {
                    "nw_src": "0.0.0.1",
                    "nw_dst": "0.0.0.2",
                    "nw_tos": 5,
                    "nw_proto": 17
                },
                "tp": {
                    "tp_src": 33948,
                    "tp_dst": 53
                }
            }
        }

        api_url = KYTOS_API + '/amlight/sdntrace/trace'
        response = requests.put(api_url, json=payload_2)
        assert response.status_code == 200, response.text
        data = response.json()
        result = self.wait_sdntrace_result(data["result"]["trace_id"])

        full_path = [
            (
                l['endpoint_b']['switch'],
                l['endpoint_b']['port_number'],
            )
            for l in self.circuit['current_path']
        ]

        actual = [
            (step['dpid'], step['port']) for step in result[1:-1]
        ]

        assert full_path != actual, f"Full path {full_path}. Actual: {actual}"
        assert full_path[:4] == actual, f"Expected {full_path[:4]}. Actual: {actual}"

        # 4. redeploy evc and check again
        circuit_id = self.circuit['id']
        api_url = KYTOS_API + '/kytos/mef_eline/v2/evc/'
        response = requests.patch(f"{api_url}/{circuit_id}/redeploy")
        assert response.status_code == 202, response.text
        time.sleep(10)
        self.circuit = self.get_evc(circuit_id)

        api_url = KYTOS_API + '/amlight/sdntrace_cp/trace'
        response = requests.put(api_url, json=payload_1)
        data = response.json()
        assert len(data["result"]) == 10, data
        expected = [
            (
                l['endpoint_b']['switch'],
                l['endpoint_b']['port_number'],
                l['metadata']['s_vlan']['value']
            )
            for l in self.circuit['current_path']
        ]
        actual = [
            (step['dpid'], step['port'], step['vlan'])
            for step in data["result"][1:]
        ]
        assert expected == actual, f"Expected {expected}. Actual: {actual}"

        api_url = KYTOS_API + '/amlight/sdntrace/trace'
        response = requests.put(api_url, json=payload_2)
        assert response.status_code == 200, response.text
        data = response.json()
        result = self.wait_sdntrace_result(data["result"]["trace_id"])
        expected = [
            (
                l['endpoint_b']['switch'],
                l['endpoint_b']['port_number'],
            )
            for l in self.circuit['current_path']
        ]
        actual = [
            (step['dpid'], step['port']) for step in result[1:-1]
        ]
        assert expected == actual, f"Expected {expected}. Actual: {actual}"

    def test_030_run_sdntrace_for_stored_flows(cls):
        """Run SDNTrace to get traces from flow_manager stored_flow"""
        cls.create_evc(100, "00:00:00:00:00:00:00:01:1", "00:00:00:00:00:00:00:0a:1")
        cls.create_evc(101, "00:00:00:00:00:00:00:01:1", "00:00:00:00:00:00:00:0a:1")
        cls.create_evc(102, "00:00:00:00:00:00:00:01:1", "00:00:00:00:00:00:00:0a:1")
        payload = [
                    {
                        "trace": {
                            "switch": {
                                "dpid": "00:00:00:00:00:00:00:01",
                                "in_port": 1
                            },
                            "eth": {
                                "dl_vlan": 100
                            }
                        }
                    },
                    {
                        "trace": {
                            "switch": {
                                "dpid": "00:00:00:00:00:00:00:01",
                                "in_port": 2
                            },
                            "eth": {
                                "dl_vlan": 101
                            }
                        }
                    },
                    {
                        "trace": {
                            "switch": {
                                "dpid": "00:00:00:00:00:00:00:0a",
                                "in_port": 1
                            }
                        }
                    },
                    {
                        "trace": {
                            "switch": {
                                "dpid": "00:00:00:00:00:00:00:0a",
                                "in_port": 1
                            }
                        }
                    }
                ]
                
        api_url = KYTOS_API + '/amlight/sdntrace_cp/traces'
        response = requests.put(api_url, json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 2
        assert "00:00:00:00:00:00:00:01" in data
        assert len(data["00:00:00:00:00:00:00:01"]) == 2
        assert "00:00:00:00:00:00:00:0a" in data
        assert len(data["00:00:00:00:00:00:00:0a"]) == 1
