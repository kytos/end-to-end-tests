import requests
import pytest
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
        """Tests if the maintenances list is empty at the beginning
        Test:
            /api/kytos/maintenance/ on GET
        """

        # Gets the maintenance schemas
        api_url = KYTOS_API + '/maintenance/'
        response = requests.get(api_url)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data == []

    def test_020_create_mw_on_switch_should_move_evc(self):
        """Tests the EVC behaviors during maintenance
        Test:
            /api/kytos/maintenance on POST
        """

        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(20)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up the maintenance window data
        payload = {
            "description": "my MW on switch 2",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'mw_id' in data

        # Waits for the MW to start
        time.sleep(mw_start_delay+5)

        # Switch 1 and 3 should have 3 flows; Switch 2 should have only 1 flow.
        s1, s2, s3 = self.net.net.get('s1', 's2', 's3')
        flows_s1 = s1.dpctl('dump-flows')
        flows_s2 = s2.dpctl('dump-flows')
        flows_s3 = s3.dpctl('dump-flows')
        assert len(flows_s1.split('\r\n ')) == 3
        assert len(flows_s3.split('\r\n ')) == 3
        assert len(flows_s2.split('\r\n ')) == 1

        # Makes sure it should be dl_vlan instead of vlan_vid
        assert 'dl_vlan=100' in flows_s1
        assert 'dl_vlan=100' in flows_s3
        assert 'dl_vlan=100' not in flows_s2

        # It makes the final and most important test: connectivity
        # 1. Creates the VLANs and set up the IP addresses
        # 2. Tries to ping to each other
        h11, h3 = self.net.net.get('h11', 'h3')
        h11.cmd('ip link add link %s name vlan100 type vlan id 100' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan100')
        h11.cmd('ip addr add 100.0.0.11/24 dev vlan100')
        h3.cmd('ip link add link %s name vlan100 type vlan id 100' % (h3.intfNames()[0]))
        h3.cmd('ip link set up vlan100')
        h3.cmd('ip addr add 100.0.0.2/24 dev vlan100')
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Waits for the MW to finish and check if the path returns to the initial configuration
        time.sleep(mw_duration)

        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s2.split('\r\n ')) == 3
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Cleans up
        h11.cmd('ip link del vlan100')
        h3.cmd('ip link del vlan100')

    def test_022_create_mw_on_switch_should_fail_dates_error(self):
        """Tests to create maintenance with the wrong payload
        Test:
            400 response calling
            /api/kytos/maintenance on POST
        """
        self.net.restart_kytos_clean()
        time.sleep(5)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up a wrong maintenance window data
        payload = {
            "description": "my MW on switch 2",
            "start": end.strftime(TIME_FMT),
            "end": start.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call is returning 201 when should be 400
    Issue #43
    """
    @pytest.mark.xfail
    def test_024_create_mw_on_switch_should_fail_items_empty(self):
        """Tests to create maintenance with the wrong payload
        Test:
            400 response calling
            /api/kytos/maintenance on POST
        """
        self.net.restart_kytos_clean()
        time.sleep(5)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up a wrong maintenance window data
        payload = {
            "description": "my MW on switch 2",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": []
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    """
    The Api call is returning 500 when should be 400
    Issue #43
    """
    @pytest.mark.xfail
    def test_026_create_mw_on_switch_should_fail_no_items_field_on_payload(self):
        """Tests to create maintenance with the wrong payload
        Test:
            400 response calling
            /api/kytos/maintenance on POST
        """
        self.net.restart_kytos_clean()
        time.sleep(5)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up a wrong maintenance window data
        payload = {
            "description": "my MW on switch 2",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT)
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 400

    def test_028_create_mw_on_switch_should_fail_payload_empty(self):
        """Tests to create maintenance with the wrong payload
        Test:
            415 response calling
            /api/kytos/maintenance on POST
        """
        self.net.restart_kytos_clean()
        time.sleep(5)

        # Sets up a wrong maintenance window data
        payload = {}

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 415

    """
    The execution breaks when should be returning a 415
    Issue #43
    """
    @pytest.mark.xfail
    def test_029_create_mw_on_switch_should_fail_wrong_payload(self):
        """Tests to create maintenance with the wrong payload
        Test:
            415 response calling
            /api/kytos/maintenance on POST
        """
        self.net.restart_kytos_clean()
        time.sleep(5)

        # Sets up a wrong maintenance window data
        payload = {"a"}

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 415

    def test_030_create_mw_on_switch_and_patch_new_end(self):
        """Tests the maintenance window data update
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
        time.sleep(20)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60

        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up the maintenance window data
        payload = {
            "description": "mw for test 030",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'mw_id' in data

        # Extracts the maintenance window id from the JSON structure
        assert len(data) == 1
        mw_id = data["mw_id"]

        # Gets the maintenance schema
        api_url = KYTOS_API + '/maintenance/' + mw_id
        response = requests.get(api_url)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data['id'] == mw_id

        # Sets up a new maintenance window data
        mw_new_end_time = 30
        new_time = end + timedelta(seconds=mw_new_end_time)
        payload1 = {
            "start": start.strftime(TIME_FMT),
            "end": new_time.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Updates the maintenance window information
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        request = requests.patch(mw_api_url, data=json.dumps(payload1), headers={'Content-type': 'application/json'})
        assert request.status_code == 201

        # Gets the maintenance window schema
        api_url = KYTOS_API + '/maintenance/' + mw_id
        response = requests.get(api_url)
        json_data = response.json()
        assert json_data['end'] == new_time.strftime(TIME_FMT)

        # Waits for the MW to start
        time.sleep(mw_start_delay + 5)

        # Verifies the flow behavior during the maintenance
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

        # Waits for the MW to finish and check if the path returns to the initial configuration
        time.sleep(mw_duration + mw_new_end_time + 5)

        # Verifies the flows behavior after the maintenance
        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s2.split('\r\n ')) == 3
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Cleans up
        h11.cmd('ip link del vlan100')
        h3.cmd('ip link del vlan100')

    def test_032_patch_non_existent_mw_on_switch_should_fail(self):
        """
        404 response calling
            /api/kytos/maintenance/{mw_id} on PATCH
        """
        self.net.restart_kytos_clean()
        time.sleep(5)

        mw_id = "c16f5bbc4d004f018a76b22f677f8c2a"

        mw_start_delay = 60
        mw_duration = 60

        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up the maintenance window data
        payload1 = {
            "description": "mw for test 030",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        request = requests.patch(mw_api_url, data=json.dumps(payload1), headers={'Content-type': 'application/json'})
        assert request.status_code == 404

    def test_034_patch_mw_on_switch_should_fail_wrong_payload_on_dates(self):
        """
        400 response calling
            /api/kytos/maintenance/{mw_id} on PATCH
        """

        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(20)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60

        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up the maintenance window data
        payload = {
            "description": "mw for test 030",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        data = response.json()

        # Extracts the maintenance window id from the JSON structure
        mw_id = data["mw_id"]

        # Sets up a new maintenance window data
        mw_new_end_time = 30
        new_time = end + timedelta(seconds=mw_new_end_time)
        payload1 = {
            "start": new_time.strftime(TIME_FMT),
            "end": start.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Updates the maintenance window information
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        request = requests.patch(mw_api_url, data=json.dumps(payload1), headers={'Content-type': 'application/json'})
        assert request.status_code == 400

        # Deletes the maintenance by its id
        api_url = KYTOS_API + '/maintenance/' + mw_id
        requests.delete(api_url)

    """
    The Api call is returning 201 when should be 400
    Issue #44
    """
    @pytest.mark.xfail
    def test_036_patch_mw_on_switch_should_fail_wrong_payload_items_empty(self):
        """
        400 response calling
            /api/kytos/maintenance/{mw_id} on PATCH
        """
        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(20)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60

        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up the maintenance window data
        payload = {
            "description": "mw for test 030",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        data = response.json()

        # Extracts the maintenance window id from the JSON structure
        mw_id = data["mw_id"]

        # Sets up a new maintenance window data
        mw_new_end_time = 30
        new_time = end + timedelta(seconds=mw_new_end_time)
        payload1 = {
            "start": start.strftime(TIME_FMT),
            "end": new_time.strftime(TIME_FMT),
            "items": []
        }

        # Updates the maintenance window information
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        request = requests.patch(mw_api_url, data=json.dumps(payload1), headers={'Content-type': 'application/json'})
        assert request.status_code == 400

        # Deletes the maintenance by its id
        api_url = KYTOS_API + '/maintenance/' + mw_id
        requests.delete(api_url)

    """
    The Api call is returning 201 when should be 400
    Issue #44
    """
    @pytest.mark.xfail
    def test_038_patch_mw_on_switch_should_fail_wrong_payload_no_items_field(self):
        """
        400 response calling
            /api/kytos/maintenance/{mw_id} on PATCH
        """
        self.net.restart_kytos_clean()
        time.sleep(5)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60

        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up the maintenance window data
        payload = {
            "description": "mw for test 030",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        data = response.json()

        # Extracts the maintenance window id from the JSON structure
        mw_id = data["mw_id"]

        # Sets up a new maintenance window data
        mw_new_end_time = 30
        new_time = end + timedelta(seconds=mw_new_end_time)
        payload1 = {
            "start": start.strftime(TIME_FMT),
            "end": new_time.strftime(TIME_FMT)
        }

        # Updates the maintenance window information
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        request = requests.patch(mw_api_url, data=json.dumps(payload1), headers={'Content-type': 'application/json'})
        assert request.status_code == 400

        # Deletes the maintenance by its id
        api_url = KYTOS_API + '/maintenance/' + mw_id
        requests.delete(api_url)

    """
    The execution breaks when should be returning a 400
    Issue https://github.com/kytos/maintenance/issues/44
    """
    @pytest.mark.xfail
    def test_039_patch_mw_on_switch_should_fail_wrong_payload(self):
        """
        400 response calling
            /api/kytos/maintenance/{mw_id} on PATCH
        """
        self.net.restart_kytos_clean()
        time.sleep(5)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60

        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up the maintenance window data
        payload = {
            "description": "mw for test 030",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        data = response.json()

        # Extracts the maintenance window id from the JSON structure
        mw_id = data["mw_id"]

        # Sets up a new maintenance window data
        payload1 = {
            "description"
        }

        # Updates the maintenance window information
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        request = requests.patch(mw_api_url, data=json.dumps(payload1), headers={'Content-type': 'application/json'})
        assert request.status_code == 400

        # Deletes the maintenance by its id
        api_url = KYTOS_API + '/maintenance/' + mw_id
        requests.delete(api_url)

    def test_040_create_mw_on_switch_and_patch_new_start_delaying_mw(self):
        """Tests the maintenance window data update
        process through MW's ID focused on the start time
        Test:
            /api/kytos/maintenance on POST,
            /api/kytos/maintenance/{mw_id} on GET, and
            /api/kytos/maintenance/{mw_id} on PATCH
        """
        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(20)

        # Sets up the maintenance window information
        mw_start_delay = 30
        mw_duration = 90
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up the maintenance window data
        payload = {
            "description": "mw for test 040",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'mw_id' in data

        # Extracts the maintenance window id from the JSON structure
        assert len(data) == 1
        mw_id = data["mw_id"]

        # Gets the maintenance schema
        api_url = KYTOS_API + '/maintenance/' + mw_id
        response = requests.get(api_url)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data['id'] == mw_id

        # Sets up a new maintenance window data
        new_start = start + timedelta(seconds=mw_start_delay)
        payload1 = {
            "start": new_start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Updates the maintenance window information
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        request = requests.patch(mw_api_url, data=json.dumps(payload1), headers={'Content-type': 'application/json'})
        assert request.status_code == 201

        # Gets the maintenance window schema
        api_url = KYTOS_API + '/maintenance/' + mw_id
        response = requests.get(api_url)
        json_data = response.json()
        assert json_data['start'] == new_start.strftime(TIME_FMT)

        # Waits for the initial MW begin time
        # (no MW, it has been changed)
        time.sleep(mw_start_delay + 5)

        s2 = self.net.net.get('s2')
        h11, h3 = self.net.net.get('h11', 'h3')
        h11.cmd('ip link add link %s name vlan100 type vlan id 100' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan100')
        h11.cmd('ip addr add 100.0.0.11/24 dev vlan100')
        h3.cmd('ip link add link %s name vlan100 type vlan id 100' % (h3.intfNames()[0]))
        h3.cmd('ip link set up vlan100')
        h3.cmd('ip addr add 100.0.0.2/24 dev vlan100')

        # Verifies the flow at the initial MW time
        # (no maintenance at that time, it has been delayed)
        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s2.split('\r\n ')) == 3
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Waits for the time in which MW will be running
        time.sleep(mw_start_delay + 5)

        # Verifies the flow during maintenance time
        flows_s2 = s2.dpctl('dump-flows')
        assert 'dl_vlan=100' not in flows_s2
        assert len(flows_s2.split('\r\n ')) == 1
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Waits for the MW to finish and check if the path returns to the initial configuration
        time.sleep(mw_duration)

        # Verifies the flow behavior after the maintenance window
        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s2.split('\r\n ')) == 3
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Cleans up
        h11.cmd('ip link del vlan100')
        h3.cmd('ip link del vlan100')

    def test_050_delete_running_mw_on_switch_should_fail(self):
        """Tests the maintenance window removing process on a running MW
        Test:
            /api/kytos/maintenance/ on POST and
            /api/kytos/maintenance/{mw_id} on DELETE

            400 response calling
            /api/kytos/maintenance/{mw_id} on DELETE
        """
        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(20)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up the maintenance window data
        payload = {
            "description": "mw for test 50",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        json_data = response.json()
        mw_id = json_data["mw_id"]

        # Waits for the MW to start
        time.sleep(mw_start_delay + 5)

        # Deletes running maintenance by its id
        api_url = KYTOS_API + '/maintenance/' + mw_id
        delete_response = requests.delete(api_url)
        assert delete_response.status_code == 400

    def test_060_delete_future_mw_on_switch(self):
        """Tests the maintenance window removing process on a scheduled MW
        Test:
            /api/kytos/maintenance/ on POST and
            /api/kytos/maintenance/{mw_id} on DELETE
        """

        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(20)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up the maintenance window data
        payload = {
            "description": "mw for test 60",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        json_data = response.json()
        mw_id = json_data["mw_id"]

        # Deletes the maintenance by its id
        api_url = KYTOS_API + '/maintenance/' + mw_id
        delete_response = requests.delete(api_url)
        assert delete_response.status_code == 200

        # Gets the maintenance window schema
        req = requests.get(api_url)
        assert req.status_code == 404

        # Waits for the time in which the MW should start (but it is deleted)
        time.sleep(mw_start_delay + 5)

        s2 = self.net.net.get('s2')
        h11, h3 = self.net.net.get('h11', 'h3')
        h11.cmd('ip link add link %s name vlan100 type vlan id 100' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan100')
        h11.cmd('ip addr add 100.0.0.11/24 dev vlan100')
        h3.cmd('ip link add link %s name vlan100 type vlan id 100' % (h3.intfNames()[0]))
        h3.cmd('ip link set up vlan100')
        h3.cmd('ip addr add 100.0.0.2/24 dev vlan100')

        # Verifies the flow behavior
        # (no maintenance at that time, it has been deleted)
        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s2.split('\r\n ')) == 3
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Cleans up
        h11.cmd('ip link del vlan100')
        h3.cmd('ip link del vlan100')

    def test_062_delete_non_existent_mw_on_switch_should_fail(self):
        """
        404 response calling
            /api/kytos/maintenance/{mw_id} on DELETE
        """
        self.net.restart_kytos_clean()
        time.sleep(5)

        mw_id = "c16f5bbc4d004f018a76b22f677f8c2a"

        # Deletes the maintenance by its id
        api_url = KYTOS_API + '/maintenance/' + mw_id
        delete_response = requests.delete(api_url)
        assert delete_response.status_code == 404

    def test_070_patch_running_mw_on_switch_should_fail(self):
        """
        Tests the patching process over a running maintenance
        400 response calling
            /api/kytos/maintenance/{mw_id} on PATCH
        """
        self.net.restart_kytos_clean()
        time.sleep(5)

        # Sets up maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        mw_new_end_time = 30
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up a maintenance window data
        payload = {
            "description": "mw for test 070",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201
        data = response.json()
        assert 'mw_id' in data

        # Extracts the maintenance window id from the JSON structure
        assert len(data) == 1
        mw_id = data["mw_id"]

        # Gets the maintenance schema
        api_url = KYTOS_API + '/maintenance/' + mw_id
        response = requests.get(api_url)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data['id'] == mw_id

        # Sets up a new maintenance window data
        new_time = end + timedelta(seconds=mw_new_end_time)
        payload1 = {
            "start": start.strftime(TIME_FMT),
            "end": new_time.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:00:02"
            ]
        }

        # Waits for the MW to start
        time.sleep(mw_start_delay + 5)

        # Updates the a running maintenance
        mw_api_url = KYTOS_API + '/maintenance/' + mw_id
        request = requests.patch(mw_api_url, data=json.dumps(payload1), headers={'Content-type': 'application/json'})
        assert request.status_code == 400

    """
    The END Api call is returning 200 when should be 201
    Issue https://github.com/kytos/maintenance/issues/35
    """
    @pytest.mark.xfail
    def test_080_end_running_mw_on_switch(self):
        """Tests the maintenance window ending process on a running MW
        Test:
            /api/kytos/maintenance/ on POST and
            /api/kytos/maintenance/{mw_id} on DELETE
        """

        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(20)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up the maintenance window data
        payload = {
            "description": "mw for test 80",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        json_data = response.json()
        mw_id = json_data["mw_id"]

        # Waits for the MW to start
        time.sleep(mw_start_delay + 5)

        # Ends a running maintenance
        api_url = KYTOS_API + '/maintenance/' + mw_id + '/end'
        end_response = requests.patch(api_url)
        assert end_response.status_code == 201 # It is returning 200

        # Waits for a time in which the MW should be running (but it is deleted)
        time.sleep(mw_duration/2)

        # Verifies the flow behavior
        s2 = self.net.net.get('s2')
        h11, h3 = self.net.net.get('h11', 'h3')
        h11.cmd('ip link add link %s name vlan100 type vlan id 100' % (h11.intfNames()[0]))
        h11.cmd('ip link set up vlan100')
        h11.cmd('ip addr add 100.0.0.11/24 dev vlan100')
        h3.cmd('ip link add link %s name vlan100 type vlan id 100' % (h3.intfNames()[0]))
        h3.cmd('ip link set up vlan100')
        h3.cmd('ip addr add 100.0.0.2/24 dev vlan100')

        flows_s2 = s2.dpctl('dump-flows')
        assert len(flows_s2.split('\r\n ')) == 3
        result = h11.cmd('ping -c1 100.0.0.2')
        assert ', 0% packet loss,' in result

        # Cleans up
        h11.cmd('ip link del vlan100')
        h3.cmd('ip link del vlan100')

    def test_082_end_non_existent_running_mw_on_switch_should_fail(self):
        """
        404 response calling
            /api/kytos/maintenance/{mw_id}/end on PATCH
        """
        self.net.restart_kytos_clean()
        time.sleep(5)

        mw_id = "c16f5bbc4d004f018a76b22f677f8c2a"

        # Ends an unknown maintenance
        api_url = KYTOS_API + '/maintenance/' + mw_id + '/end'
        end_response = requests.patch(api_url)
        assert end_response.status_code == 404

    def test_084_end_not_running_mw_on_switch_should_fail(self):
        """Tests the maintenance window ending process on a not running MW
        Test:
            400 response calling
            /api/kytos/maintenance/{mw_id}/end on PATCH
        """

        self.net.restart_kytos_clean()
        time.sleep(5)
        self.create_circuit(100)
        time.sleep(20)

        # Sets up the maintenance window information
        mw_start_delay = 60
        mw_duration = 60
        start = datetime.now() + timedelta(seconds=mw_start_delay)
        end = start + timedelta(seconds=mw_duration)

        # Sets up the maintenance window data
        payload = {
            "description": "mw for test 80",
            "start": start.strftime(TIME_FMT),
            "end": end.strftime(TIME_FMT),
            "items": [
                "00:00:00:00:00:00:02"
            ]
        }

        # Creates a new maintenance window
        api_url = KYTOS_API + '/maintenance/'
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        json_data = response.json()
        mw_id = json_data["mw_id"]

        # Ends a not running maintenance
        api_url = KYTOS_API + '/maintenance/' + mw_id + '/end'
        end_response = requests.patch(api_url)
        assert end_response.status_code == 400

        # Deletes the maintenance by its id
        api_url = KYTOS_API + '/maintenance/' + mw_id
        requests.delete(api_url)

    # def test_090_extend_running_mw_on_switch(self):
    #     pass
