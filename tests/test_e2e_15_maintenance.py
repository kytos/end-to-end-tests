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
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:01:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:02:2"}},
                {"endpoint_a": {"id": "00:00:00:00:00:00:00:02:3"},
                 "endpoint_b": {"id": "00:00:00:00:00:00:00:03:2"}}
            ],
        }
        api_url = KYTOS_API+'/mef_eline/v2/evc/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})

    def test_010_list_mw_should_be_empty(self):
        """Test if the maintenances list is empty at the beginning
        Test:
            /api/kytos/maintenance/ on GET
        """

        # Get the maintenance schemas
        api_url = KYTOS_API + '/maintenance/'
        response = requests.get(api_url)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data == []

    def test_020_create_mw_on_switch_should_move_evc(self):
        """Test the EVC behaviors during maintenances
        Test:
            /api/kytos/maintenance on POST
        """

        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(20)

        # Setup maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Setup maintenance window data
        payload = {
            "description": "my MW on switch 2",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Create a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'mw_id' in data

        # wait the MW to begin
        time.sleep(mw_start_delay+5)

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
        time.sleep(mw_duration)

        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s2.split('\r\n ')) == 3
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # clean up
        h11.cmd('ip link del vlan100')
        h3.cmd('ip link del vlan100')

    def test_030_create_mw_on_switch_and_patch_new_end(self):
        """Test the maintenance window data update
        process through MW Id focused on the end time
        Test:
            /api/kytos/maintenance on POST and
            /api/kytos/maintenance/{mw_id} on PATCH
        supported by
            /api/kytos/maintenance on GET
        """
        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(10)

        # Setup maintenance window information
        mw_start_delay = 60
        mw_duration = 60

        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Setup maintenance window data
        payload = {
            "description": "mw for test 030",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Create a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'mw_id' in data

        # Extract the maintenance window id from the JSON structure
        assert len(data) == 1
        mw_id = data["mw_id"]

        # Get the maintenance schemas
        api_url = KYTOS_API + '/maintenance/' + mw_id
        response = requests.get(api_url)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data['id'] == mw_id

        # Setup new maintenance window data
        mw_new_end_time = 30
        new_time = end + timedelta(seconds=mw_new_end_time)
        payload1 = {
            "start": start.strftime(TIME_FMT),
            "end": new_time.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Update maintenance window information
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        request = requests.patch(mw_api_url, data=json.dumps(payload1), headers={'Content-type': 'application/json'})
        assert request.status_code == 201

        # Get maintenance window schema
        api_url = KYTOS_API + '/maintenance/' + mw_id
        response = requests.get(api_url)
        json_data = response.json()
        assert json_data['end'] == new_time.strftime(TIME_FMT)

        # Wait the MW to begin
        time.sleep(mw_start_delay + 5)

        # Verify flows during maintenance
        s2 = self.net.net.get('s2')
        flows_s2 = s2.dpctl('dump-flows')
        assert 'dl_vlan=100' not in flows_s2
        assert len(flows_s2.split('\r\n ')) == 1

        h11, h3 = self.net.net.get('h11', 'h3')
        h11.cmd('ip link add link %s name vlan100 type vlan id 100' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan100')
        h11.cmd('ip addr add 100.0.0.11/24 dev vlan100')
        h3.cmd('ip link add link %s name vlan100 type vlan id 100' % (h3.intfNames()[0]))
        h3.cmd('ip link set up vlan100')
        h3.cmd('ip addr add 100.0.0.2/24 dev vlan100')
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Wait for the MW to finish and check if the path returned to pass through sw2
        time.sleep(mw_duration + mw_new_end_time + 5)

        # Verify flows behavior after maintenance
        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s2.split('\r\n ')) == 3
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Clean up
        h11.cmd('ip link del vlan100')
        h3.cmd('ip link del vlan100')

    def test_040_create_mw_on_switch_and_patch_new_start_delaying_mw(self):
        """Test the maintenance window data update
        process through MW Id focused on the start time
        Test:
            /api/kytos/maintenance on POST and
            /api/kytos/maintenance/{mw_id} on GET
            /api/kytos/maintenance/{mw_id} on PATCH
        """
        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(10)

        # Setup maintenance window information
        mw_start_delay = 30
        mw_duration = 90
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Setup maintenance window data
        payload = {
            "description": "mw for test 040",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Create a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'mw_id' in data

        # Extract the maintenance window id from the JSON structure
        assert len(data) == 1
        mw_id = data["mw_id"]

        # Get the maintenance schemas
        api_url = KYTOS_API + '/maintenance/' + mw_id
        response = requests.get(api_url)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data['id'] == mw_id

        # Setup new maintenance window data
        new_start = start + timedelta(seconds=mw_start_delay)
        payload1 = {
            "start": new_start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Update maintenance window information
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        request = requests.patch(mw_api_url, data=json.dumps(payload1), headers={'Content-type': 'application/json'})
        assert request.status_code == 201

        # Get maintenance window schema
        api_url = KYTOS_API + '/maintenance/' + mw_id
        response = requests.get(api_url)
        json_data = response.json()
        assert json_data['start'] == new_start.strftime(TIME_FMT)

        # Wait for the initial MW begin time
        time.sleep(mw_start_delay + 5)

        s2 = self.net.net.get('s2')
        h11, h3 = self.net.net.get('h11', 'h3')
        h11.cmd('ip link add link %s name vlan100 type vlan id 100' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan100')
        h11.cmd('ip addr add 100.0.0.11/24 dev vlan100')
        h3.cmd('ip link add link %s name vlan100 type vlan id 100' % (h3.intfNames()[0]))
        h3.cmd('ip link set up vlan100')
        h3.cmd('ip addr add 100.0.0.2/24 dev vlan100')

        # It verifies the flow at the initial MW time
        # (no maintenance at that time, it has been delayed)
        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s2.split('\r\n ')) == 3
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Wait for a time in which MW will be running
        time.sleep(mw_start_delay + 5)

        # Verify flows during maintenance time
        flows_s2 = s2.dpctl('dump-flows')
        assert 'dl_vlan=100' not in flows_s2
        assert len(flows_s2.split('\r\n ')) == 1
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Wait for the MW to finish and check if the path returned to its initial route through sw2
        time.sleep(mw_duration)

        # It verifies flows behavior after maintenance window
        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s2.split('\r\n ')) == 3
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Clean up
        h11.cmd('ip link del vlan100')
        h3.cmd('ip link del vlan100')

    def test_050_delete_running_mw_on_switch_should_fail(self):
        """Test the maintenance window removing process on a running MW
        Test:
            /api/kytos/maintenance on POST and
            /api/kytos/maintenance/{mw_id} on GET
            /api/kytos/maintenance/{mw_id} on PATCH
        """
        # Setup maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Setup maintenance window data
        payload = {
            "description": "mw for test 50",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:02"
            ]
        }

        # Create a new maintenance window
        api_url = KYTOS_API + '/maintenance/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        json_data = response.json()
        mw_id = json_data["mw_id"]

        # Wait the MW to begin
        time.sleep(mw_start_delay + 5)

        # Delete a running mw_id
        api_url = KYTOS_API + '/maintenance/' + mw_id
        delete_response = requests.delete(api_url)
        assert delete_response.status_code == 400

    def test_060_delete_future_mw_on_switch(self):

        # Setup maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Setup maintenance window data
        payload = {
            "description": "mw for test 60",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:02"
            ]
        }

        # Create a new maintenance window
        api_url = KYTOS_API + '/maintenance/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        json_data = response.json()
        mw_id = json_data["mw_id"]

        # Delete MW
        api_url = KYTOS_API + '/maintenance/' + mw_id
        delete_response = requests.delete(api_url)
        assert delete_response.status_code == 200

        # Get maintenance window schema
        req = requests.get(api_url)
        assert req.status_code == 404

    def test_070_patch_running_mw_on_switch_should_fail(self):

        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(10)

        # Setup maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        mw_new_end_time = 30
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Setup maintenance window data
        payload = {
            "description": "mw for test 070",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Create a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'mw_id' in data

        # Extract the maintenance window id from the JSON structure
        assert len(data) == 1
        mw_id = data["mw_id"]

        # Get the maintenance schemas
        api_url = KYTOS_API + '/maintenance/' + mw_id
        response = requests.get(api_url)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data['id'] == mw_id

        # Setup new maintenance window data
        new_time = end + timedelta(seconds=mw_new_end_time)
        payload1 = {
            "start": start.strftime(TIME_FMT),
            "end": new_time.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Wait the MW to begin
        time.sleep(mw_start_delay + 5)

        # Update maintenance window information
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        request = requests.patch(mw_api_url, data=json.dumps(payload1), headers={'Content-type': 'application/json'})
        assert request.status_code == 400

    def test_080_end_running_mw_on_switch(self):
        pass

    def test_090_extend_running_mw_on_switch(self):
        pass
