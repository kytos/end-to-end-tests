import requests
from tests.helpers import NetworkTest
import time
import json
from datetime import datetime, timedelta

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % CONTROLLER

TIME_FMT = "%Y-%m-%dT%H:%M:%S+0000"


class TestE2EMaintenance:
    net = None

    @classmethod
    def setup_class(cls):
        cls.net = NetworkTest(CONTROLLER)
        cls.net.start()
        cls.net.restart_kytos_clean()
        time.sleep(10)

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def create_circuit(self, vlan_id):
        payload = {
            "name": "my evc1",
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": "00:00:00:00:00:00:00:01:1",
                "tag": {
                    "tag_type": 1,
                    "value": vlan_id
                }
            },
            "uni_z": {
                "interface_id": "00:00:00:00:00:00:00:03:1",
                "tag": {
                    "tag_type": 1,
                    "value": vlan_id
                }
            },
            "primary_path": [
                {"endpoint_a": {"interface_id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"interface_id": "00:00:00:00:00:00:00:02:2"}},
                {"endpoint_a": {"interface_id": "00:00:00:00:00:00:00:02:3"},
                 "endpoint_b": {"interface_id": "00:00:00:00:00:00:00:03:2"}}
            ],
        }
        api_url = KYTOS_API+'/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})

    def test_001_list_mw_should_be_empty(self):
        """Test if list maintenances is empty at the begin ."""
        assert True

    def test_010_create_mw_on_switch_should_move_evc(self):
        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(20)

        start = datetime.now() + timedelta(seconds=60)
        end = start + timedelta(seconds=60)
        payload = {
            "description": "my MW on switch 2",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:02"
            ]
        }
        api_url = KYTOS_API+'/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'mw_id' in data

        # wait the MW to begin
        time.sleep(80)

        # switch 1 and 3 should have 3 flows, switch 2 should have only 1 flow
        s1, s2, s3 = self.net.net.get('s1', 's2', 's3')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        flows_s3 = s3.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s3.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 1

        # make sure it should be dl_vlan instead of vlan_vid
        assert 'dl_vlan=100' in flows_s1
        assert 'dl_vlan=100' in flows_s3
        assert 'dl_vlan=100' not in flows_s2

        # Make the final and most important test: connectivity
        # 1. create the vlans and setup the ip addresses
        # 2. try to ping each other
        h11, h3 = self.net.net.get('h11', 'h3')
        h11.cmd('ip link add link %s name vlan100 type vlan id 100' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan100')
        h11.cmd('ip addr add 100.0.0.11/24 dev vlan100')
        h3.cmd('ip link add link %s name vlan100 type vlan id 100' % (h3.intfNames()[0]))
        h3.cmd('ip link set up vlan100')
        h3.cmd('ip addr add 100.0.0.2/24 dev vlan100')
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # wait more 60s to the MW to finish and check if the path returned to pass through sw2
        time.sleep(60)

        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s2.split('\r\n ')) == 3
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # clean up
        h11.cmd('ip link del vlan100')
        h3.cmd('ip link del vlan100')

    def test_011_delete_mw_on_switch(self):
        # 0. Start maintenance window
        start = datetime.now() + timedelta(seconds=60)
        end = start + timedelta(seconds=60)
        payload = {
            "description": "mw for test 11",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:02"
            ]
        }

        api_url = KYTOS_API + '/maintenance/'
        # 1 Send request to API to create maintenance schema
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        # 2. from the output of the POST request, extract the mw_id
        json_data = response.json()
        mw_id = json_data["mw_id"]
        # 3. Provide mw_id to API call to delete said mw_id
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        delete_response = requests.delete(mw_api_url, data=json.dumps(payload),
                                          headers={'Content-type': 'application/json'})
        # 4. Verify that code 200(success) is given back
        assert delete_response.status_code == 200
        # 5. Request the deleted maintenance window, and verify that the mw_id is not found therefore causing a 404.
        req = requests.get(mw_api_url)
        assert req.status_code == 404

    def test_012_patch_mw_on_switch(self):
        """Update data of the maintenance window with the ID provided by the user"""
        # 0. Start maintenance window
        start = datetime.now() + timedelta(seconds=60)
        end = start + timedelta(seconds=60)
        payload = {
            "description": "mw for test 12",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:02"
            ]
        }

        api_url = KYTOS_API + '/maintenance/'
        # 1 Send request to API to create maintenance schema
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        # 2. from the output of the POST request, extract the mw_id
        json_data = response.json()
        mw_id = json_data["mw_id"]
        #  3. Provide mw_id to API call to update said mw_id
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        # 4. Send new payload containing new end_time via a patch req
        new_time = datetime.now()
        payload1 = {
            "start": start.strftime(TIME_FMT),
            "end": new_time.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:02"
            ]
        }
        request = requests.patch(mw_api_url, data=json.dumps(payload1), headers={'Content-type': 'application/json'})
        assert request.status_code == 201
        # 5. Re-start Kytos to allow for changes to take place
        self.net.start_controller()
        self.net.wait_switches_connect()
        # 6. Request maintenance window and validate changed attribute
        req = requests.get(mw_api_url)
        json_data = req.json()
        for attribute in json_data:
            if attribute['end'] == new_time:
                print("Maintenance window CHANGED correctly")

    def test_013_patch_end_mw_on_switch(self):
        """Send request to finish a maintenance window right now"""
        # 0. Start maintenance window
        start = datetime.now() + timedelta(seconds=60)
        end = start + timedelta(seconds=60)
        payload = {
            "description": "mw for test 13",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:02"
            ]
        }

        api_url = KYTOS_API + '/maintenance/'
        # 1 Send request to API to create maintenance schema
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        # 2. from the output of the POST request, extract the mw_id
        json_data = response.json()
        mw_id = json_data["mw_id"]
        #  3. Provide mw_id to API call to update a specific mw
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id + '/end'
        request = requests.patch(mw_api_url, headers={'Content-type': 'application/json'})
        assert request.status_code == 201
        # 4. Re-start Kytos to allow for changes to take place
        self.net.start_controller()
        self.net.wait_switches_connect()
        # 5. Request the ended maintenance window, and verify that it was properly ended.
        ended_api_url = KYTOS_API + '/maintenance/' + mw_id
        req = requests.get(ended_api_url)
        # Status may be PENDING when starting, RUNNING when its running, and FINISHED when ended.
        if req['status'] == "FINISHED":
            return
        else:
            raise Exception("Maintenance window did not end properly")
