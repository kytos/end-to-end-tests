import json
import time

import requests

from tests.helpers import NetworkTest

CONTROLLER = "127.0.0.1"
KYTOS_API = "http://%s:8181/api/kytos" % CONTROLLER


class TestE2EMefEline:
    net = None

    def setup_method(self, method):
        """
        It is called at the beginning of every class method execution
        """
        self.net.start_controller(clean_config=True, enable_all=True)
        self.net.wait_switches_connect()
        time.sleep(10)

    @classmethod
    def setup_class(cls):
        cls.net = NetworkTest(CONTROLLER, topo_name="ring")
        cls.net.start()
        cls.net.restart_kytos_clean()
        cls.net.wait_switches_connect()
        time.sleep(5)

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def restart(self, _clean_config=False, _enable_all=True):
        self.net.start_controller(clean_config=_clean_config, enable_all=_enable_all)
        self.net.wait_switches_connect()
        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

    def add_topology_metadata(self):
        """Add topology metadata."""
        links_metadata = {
            "78282c4d5b579265f04ebadc4405ca1b49628eb1d684bb45e5d0607fa8b713d0": {
                "link_name": "s1-eth3-s2-eth2",
                "ownership": "red",
            },
            "c8b55359990f89a5849813dc348d30e9e1f991bad1dcb7f82112bd35429d9b07": {
                "link_name": "s1-eth4-s3-eth3",
                "ownership": "blue",
            },
            "4d42dc0852278accac7d9df15418f6d921db160b13d674029a87cef1b5f67f30": {
                "link_name": "s2-eth3-s3-eth2",
                "ownership": "red",
            },
        }

        for link_id, metadata in links_metadata.items():
            api_url = f"{KYTOS_API}/topology/v3/links/{link_id}/metadata"
            response = requests.post(
                api_url,
                data=json.dumps(metadata),
                headers={"Content-type": "application/json"},
            )
            assert response.status_code == 201, response.text
        return links_metadata

    def create_evc(
        self,
        uni_a="00:00:00:00:00:00:00:01:1",
        uni_z="00:00:00:00:00:00:00:03:1",
        vlan_id=100,
        primary_constraints=None,
        secondary_constraints=None,
    ):
        payload = {
            "name": "Vlan_%s" % vlan_id,
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {"interface_id": uni_a, "tag": {"tag_type": 1, "value": vlan_id}},
            "uni_z": {"interface_id": uni_z, "tag": {"tag_type": 1, "value": vlan_id}},
        }
        if primary_constraints:
            payload.update({"primary_constraints": primary_constraints})
        if secondary_constraints:
            payload.update({"secondary_constraints": secondary_constraints})
        api_url = KYTOS_API + "/mef_eline/v2/evc/"
        response = requests.post(api_url, json=payload)
        assert response.status_code == 201, response.text
        data = response.json()
        return data["circuit_id"]

    def update_evc(self, circuit_id: str, **kwargs) -> dict:
        """Update an EVC."""
        api_url = f"{KYTOS_API}/mef_eline/v2/evc/{circuit_id}"
        response = requests.patch(api_url, json=kwargs)
        assert response.status_code == 200, response.text
        data = response.json()
        return data

    def delete_evc(self, circuit_id) -> dict:
        """Delete an EVC."""
        api_url = f"{KYTOS_API}/mef_eline/v2/evc/{circuit_id}"
        response = requests.delete(api_url)
        assert response.status_code == 200, response.text
        data = response.json()
        return data

    def test_001_create_update_with_constraints(self):
        """Test to create -> update with constraints."""

        links_metadata = self.add_topology_metadata()
        blue_link_ids, red_link_ids = set(), set()
        for k, v in links_metadata.items():
            if "ownership" not in v:
                continue
            if v["ownership"] == "blue":
                blue_link_ids.add(k)
            if v["ownership"] == "red":
                red_link_ids.add(k)

        api_url = KYTOS_API + "/mef_eline/v2/evc/"
        evc_id = self.create_evc(
            uni_a="00:00:00:00:00:00:00:01:1",
            uni_z="00:00:00:00:00:00:00:03:1",
            vlan_id=100,
            primary_constraints={"mandatory_metrics": {"ownership": "red"}},
            secondary_constraints={"mandatory_metrics": {"ownership": "blue"}},
        )

        time.sleep(10)
        response = requests.get(api_url + evc_id)
        data = response.json()
        assert data["enabled"]
        assert data["active"]
        assert data["current_path"], data["current_path"]
        assert data["failover_path"], data["failover_path"]
        assert data["primary_constraints"] == {
            "mandatory_metrics": {"ownership": "red"},
            "spf_attribute": "hop",
        }
        assert data["secondary_constraints"] == {
            "mandatory_metrics": {"ownership": "blue"},
            "spf_attribute": "hop",
        }

        # assert current_path and failover_path expected paths
        current_path_ids = {link["id"] for link in data["current_path"]}
        failover_path_ids = {link["id"] for link in data["failover_path"]}

        assert current_path_ids == red_link_ids, current_path_ids
        assert failover_path_ids == blue_link_ids, failover_path_ids

        # update the EVC switching the primary and secondary constraints
        evc_id = self.update_evc(
            evc_id,
            primary_constraints={
                "mandatory_metrics": {"ownership": "blue"},
                "spf_attribute": "hop",
            },
            secondary_constraints={
                "mandatory_metrics": {"ownership": "red"},
                "spf_attribute": "hop",
            },
        )
        time.sleep(10)
        response = requests.get(api_url + evc_id)
        data = response.json()
        assert data["enabled"]
        assert data["active"]
        assert data["current_path"], data["current_path"]
        assert data["failover_path"], data["failover_path"]
        assert data["primary_constraints"] == {
            "mandatory_metrics": {"ownership": "blue"},
            "spf_attribute": "hop",
        }
        assert data["secondary_constraints"] == {
            "mandatory_metrics": {"ownership": "red"},
            "spf_attribute": "hop",
        }

        # assert current_path and failover_path expected paths
        current_path_ids = {link["id"] for link in data["current_path"]}
        failover_path_ids = {link["id"] for link in data["failover_path"]}
        assert current_path_ids == blue_link_ids, current_path_ids
        assert failover_path_ids == red_link_ids, failover_path_ids
