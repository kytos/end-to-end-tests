import json
import requests
from tests.helpers import NetworkTest
import time

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % CONTROLLER


class TestE2ETopology:
    net = None

    def setup_method(self, method):
        """
        It is called at the beginning of every class method execution
        """
        # Start the controller setting an environment in
        # which all elements are disabled in a clean setting
        self.net.start_controller(clean_config=True, enable_all=False)
        self.net.wait_switches_connect()
        time.sleep(10)

    @classmethod
    def setup_class(cls):
        cls.net = NetworkTest(CONTROLLER)
        cls.net.start()
        cls.net.wait_switches_connect()
        time.sleep(5)

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def test_010_list_switches(self):
        """
        Test /api/kytos/topology/v3/ on GET
        """
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()

        assert response.status_code == 200
        assert 'switches' in data
        assert len(data['switches']) == 3
        assert '00:00:00:00:00:00:00:01' in data['switches']
        assert '00:00:00:00:00:00:00:02' in data['switches']
        assert '00:00:00:00:00:00:00:03' in data['switches']

    def test_020_enabling_switch_persistent(self):
        """
        Test /api/kytos/topology/v3/switches/{dpid}/enable on POST
        supported by
            /api/kytos/topology/v3/switches on GET
        """

        switch_id = '00:00:00:00:00:00:00:01'

        # Make sure the switches are disabled by default
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        assert data['switches'][switch_id]['enabled'] is False

        # Enable the switches
        api_url = KYTOS_API + '/topology/v3/switches/%s/enable' % switch_id
        response = requests.post(api_url)
        assert response.status_code == 201

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Check if the switches are enabled
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        assert data['switches'][switch_id]['enabled'] is True

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Check if the switches are still enabled and now with the links
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        assert data['switches'][switch_id]['enabled'] is True

    def test_030_disabling_switch_persistent(self):
        """
        Test /api/kytos/topology/v3/switches/{dpid}/disable on POST
        supported by
            /api/kytos/topology/v3/switches on GET
        """

        switch_id = "00:00:00:00:00:00:00:01"

        # Enable the switch
        api_url = KYTOS_API + '/topology/v3/switches/%s/enable' % switch_id
        response = requests.post(api_url)
        assert response.status_code == 201

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Check if the switch is enabled
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()

        assert response.status_code == 200
        assert data['switches'][switch_id]['enabled'] is True

        # Disable the switch and check if the switch is really disabled
        api_url = KYTOS_API + '/topology/v3/switches/%s/disable' % switch_id
        response = requests.post(api_url)
        assert response.status_code == 201

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()
        assert data['switches'][switch_id]['enabled'] is False

    def test_040_removing_switch_metadata_persistent(self):
        """
        Test /api/kytos/topology/v3/switches/{dpid}/metadata/{key} on DELETED
        supported by:
            /api/kytos/topology/v3/switches/{dpid}/metadata on POST
            and
            /api/kytos/topology/v3/switches/{dpid}/metadata on GET
        """

        switch_id = "00:00:00:00:00:00:00:01"

        # Insert switch metadata
        payload = {"tmp_key": "tmp_value"}
        key = next(iter(payload))
        api_url = KYTOS_API + '/topology/v3/switches/%s/metadata' % switch_id
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Verify that the metadata is inserted
        api_url = KYTOS_API + '/topology/v3/switches/%s/metadata' % switch_id
        response = requests.get(api_url)
        data = response.json()
        keys = data['metadata'].keys()
        assert key in keys

        # Delete the switch metadata
        api_url = KYTOS_API + '/topology/v3/switches/%s/metadata/%s' % (switch_id, key)
        response = requests.delete(api_url)
        assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Make sure the metadata is removed
        api_url = KYTOS_API + '/topology/v3/switches/%s/metadata' % switch_id
        response = requests.get(api_url)
        data = response.json()
        keys = data['metadata'].keys()
        assert key not in keys

    def test_050_enabling_interface_persistent(self):
        """
        Test /api/kytos/topology/v3/interfaces/{interface_id}/enable on POST
        supported by
            /api/kytos/topology/v3/interfaces on GET
        """

        # Make sure the interfaces are disabled
        api_url = KYTOS_API + '/topology/v3/interfaces'
        response = requests.get(api_url)
        data = response.json()
        for interface in data['interfaces']:
            assert data['interfaces'][interface]['enabled'] is False

        interface_id = "00:00:00:00:00:00:00:01:4"

        # Enable the interface
        api_url = KYTOS_API + '/topology/v3/interfaces/%s/enable' % interface_id
        response = requests.post(api_url)
        assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Check if the interface is enabled
        api_url = KYTOS_API + '/topology/v3/interfaces'
        response = requests.get(api_url)
        data = response.json()
        assert data['interfaces'][interface_id]['enabled'] is True

    def test_060_enabling_all_interfaces_on_a_switch_persistent(self):
        """
        Test /api/kytos/topology/v3/interfaces/switch/{dpid}/enable on POST
        supported by
            /api/kytos/topology/v3/switches on GET
        """

        switch_id = "00:00:00:00:00:00:00:01"

        # Make sure all the interfaces belonging to the target switch are disabled
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()

        for interface in data['switches'][switch_id]['interfaces']:
            assert data['switches'][switch_id]['interfaces'][interface]['enabled'] is False

        # Enabling all the interfaces
        api_url = KYTOS_API + '/topology/v3/interfaces/switch/%s/enable' % switch_id
        response = requests.post(api_url)
        assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Make sure all the interfaces belonging to the target switch are enabled
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()

        for interface in data['switches'][switch_id]['interfaces']:
            assert data['switches'][switch_id]['interfaces'][interface]['enabled'] is True

    def test_070_disabling_interface_persistent(self):
        """
        Test /api/kytos/topology/v3/interfaces/{interface_id}/disable on POST
        supported by:
            /api/kytos/topology/v3/interfaces/{interface_id}/enable on POST
            and
            /api/kytos/topology/v3/interfaces on GET
        """
        interface_id = "00:00:00:00:00:00:00:01:4"

        # Enable the interface
        api_url = KYTOS_API + '/topology/v3/interfaces/%s/enable' % interface_id
        response = requests.post(api_url)
        assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Check if the interface is enabled
        api_url = KYTOS_API + '/topology/v3/interfaces'
        response = requests.get(api_url)
        data = response.json()
        assert data['interfaces'][interface_id]['enabled'] is True

        # Disable the interface and check if the interface is really disabled
        api_url = KYTOS_API + '/topology/v3/interfaces/%s/disable' % interface_id
        response = requests.post(api_url)
        assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        api_url = KYTOS_API + '/topology/v3/interfaces'
        response = requests.get(api_url)
        data = response.json()
        assert data['interfaces'][interface_id]['enabled'] is False

    def test_080_disabling_all_interfaces_on_a_switch_persistent(self):
        """
        Test /api/kytos/topology/v3/interfaces/{interface_id}/disable on POST
        supported by:
            /api/kytos/topology/v3/interfaces/switch/{dpid}/enable on POST
            and
            /api/kytos/topology/v3/switches on GET
        """

        switch_id = "00:00:00:00:00:00:00:01"

        # Enabling all the interfaces
        api_url = KYTOS_API + '/topology/v3/interfaces/switch/%s/enable' % switch_id
        response = requests.post(api_url)
        assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Make sure all the interfaces belonging to the target switch are enabled
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()

        for interface in data['switches'][switch_id]['interfaces']:
            assert data['switches'][switch_id]['interfaces'][interface]['enabled'] is True

    def test_090_removing_interfaces_metadata_persistent(self):
        """
        Test /api/kytos/topology/v3/interfaces/{interface_id}/metadata/{key} on DELETE
        supported by:
            /api/kytos/topology/v3/interfaces/{interface_id}/metadata on POST
            and
            /api/kytos/topology/v3/interfaces/{interface_id}/metadata on GET
        """
        # It fails due to a bug, reported to Kytos team

        interface_id = "00:00:00:00:00:00:00:01:4"

        # Insert interface metadata
        payload = {"tmp_key": "tmp_value"}
        key = next(iter(payload))

        api_url = KYTOS_API + '/topology/v3/interfaces/%s/metadata' % interface_id
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Verify that the metadata is inserted
        api_url = KYTOS_API + '/topology/v3/interfaces/%s/metadata' % interface_id
        response = requests.get(api_url)
        data = response.json()
        keys = data['metadata'].keys()
        assert key in keys

        # Delete the interface metadata
        api_url = KYTOS_API + '/topology/v3/interfaces/%s/metadata/%s' % (interface_id, key)
        response = requests.delete(api_url)
        assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Make sure the metadata is removed
        api_url = KYTOS_API + '/topology/v3/interfaces/%s/metadata' % interface_id
        response = requests.get(api_url)
        data = response.json()
        keys = data['metadata'].keys()
        assert key not in keys

    def test_100_enabling_link_persistent(self):
        """
        Test /api/kytos/topology/v3/links/{link_id}/enable on POST
        supported by:
            /api/kytos/topology/v3/links on GET
        """

        endpoint_a = '00:00:00:00:00:00:00:01:3'
        endpoint_b = '00:00:00:00:00:00:00:02:2'

        # make sure the links are disabled by default
        api_url = KYTOS_API + '/topology/v3/links'
        response = requests.get(api_url)
        data = response.json()

        assert response.status_code == 200
        assert len(data['links']) == 0

        # Need to enable the switches and ports first
        for i in [1, 2, 3]:
            sw = "00:00:00:00:00:00:00:0%d" % i

            api_url = KYTOS_API + '/topology/v3/switches/%s/enable' % sw
            response = requests.post(api_url)
            assert response.status_code == 201

            api_url = KYTOS_API + '/topology/v3/interfaces/switch/%s/enable' % sw
            response = requests.post(api_url)
            assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # now all the links should stay disabled
        api_url = KYTOS_API + '/topology/v3/links'
        response = requests.get(api_url)
        data = response.json()
        assert len(data['links']) == 3

        link_id1 = None
        for k, v in data['links'].items():
            link_a, link_b = v['endpoint_a']['id'], v['endpoint_b']['id']
            if {link_a, link_b} == {endpoint_a, endpoint_b}:
                link_id1 = k
        assert link_id1 is not None
        assert data['links'][link_id1]['enabled'] is False

        api_url = KYTOS_API + '/topology/v3/links/%s/enable' % link_id1
        response = requests.post(api_url)
        assert response.status_code == 201

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # check if the links are now enabled
        api_url = KYTOS_API + '/topology/v3/links'
        response = requests.get(api_url)
        data = response.json()
        assert data['links'][link_id1]['enabled'] is True

    def test_110_disabling_link_persistent(self):
        """
        Test /api/kytos/topology/v3/links/{link_id}/disable on POST
        supported by:
            /api/kytos/topology/v3/links on GET
            and
            /api/kytos/topology/v3/links/{link_id}/enable on POST
        """

        endpoint_a = '00:00:00:00:00:00:00:01:3'
        endpoint_b = '00:00:00:00:00:00:00:02:2'

        # make sure the links are disabled by default
        api_url = KYTOS_API + '/topology/v3/links'
        response = requests.get(api_url)
        data = response.json()

        assert response.status_code == 200
        assert len(data['links']) == 0

        # enable the links (need to enable the switches and ports first)
        for i in [1, 2, 3]:
            sw = "00:00:00:00:00:00:00:0%d" % i

            api_url = KYTOS_API + '/topology/v3/switches/%s/enable' % sw
            response = requests.post(api_url)
            assert response.status_code == 201

            api_url = KYTOS_API + '/topology/v3/interfaces/switch/%s/enable' % sw
            response = requests.post(api_url)
            assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # now all the links should stay disabled
        api_url = KYTOS_API + '/topology/v3/links'
        response = requests.get(api_url)
        data = response.json()
        assert len(data['links']) == 3

        link_id1 = None
        for k, v in data['links'].items():
            link_a, link_b = v['endpoint_a']['id'], v['endpoint_b']['id']
            if {link_a, link_b} == {endpoint_a, endpoint_b}:
                link_id1 = k
        assert link_id1 is not None
        assert data['links'][link_id1]['enabled'] is False

        api_url = KYTOS_API + '/topology/v3/links/%s/enable' % link_id1
        response = requests.post(api_url)
        assert response.status_code == 201

        # check if the links are now enabled
        api_url = KYTOS_API + '/topology/v3/links'
        response = requests.get(api_url)
        data = response.json()
        assert data['links'][link_id1]['enabled'] is True

        # restart kytos and check if the links are still enabled
        self.net.start_controller(clean_config=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # check if the links are still enabled and now with the links
        api_url = KYTOS_API + '/topology/v3/links'
        response = requests.get(api_url)
        data = response.json()
        assert data['links'][link_id1]['enabled'] is True

        # disable the link
        api_url = KYTOS_API + '/topology/v3/links/%s/disable' % link_id1
        response = requests.post(api_url)
        assert response.status_code == 201

        # restart kytos and check if the links are still enabled
        self.net.start_controller(clean_config=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # check if the links are still enabled and now with the links
        api_url = KYTOS_API + '/topology/v3/links'
        response = requests.get(api_url)
        data = response.json()
        assert data['links'][link_id1]['enabled'] is False

    def test_120_removing_link_metadata_persistent(self):
        """
        Test /api/kytos/topology/v3/links/{link_id}/metadata/{key} on DELETE
        supported by:
            /api/kytos/topology/v3/links/{link_id}/metadata on POST
            and
            /api/kytos/topology/v3/links/{link_id}/metadata on GET
        """

        endpoint_a = '00:00:00:00:00:00:00:01:3'
        endpoint_b = '00:00:00:00:00:00:00:02:2'

        # Enable the switches and ports first
        for i in [1, 2, 3]:
            sw = "00:00:00:00:00:00:00:0%d" % i

            api_url = KYTOS_API + '/topology/v3/switches/%s/enable' % sw
            response = requests.post(api_url)
            assert response.status_code == 201

            api_url = KYTOS_API + '/topology/v3/interfaces/switch/%s/enable' % sw
            response = requests.post(api_url)
            assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Get the link_id
        api_url = KYTOS_API + '/topology/v3/links'
        response = requests.get(api_url)
        data = response.json()

        link_id1 = None
        for k, v in data['links'].items():
            link_a, link_b = v['endpoint_a']['id'], v['endpoint_b']['id']
            if {link_a, link_b} == {endpoint_a, endpoint_b}:
                link_id1 = k

        # Enable the link_id
        api_url = KYTOS_API + '/topology/v3/links/%s/enable' % link_id1
        response = requests.post(api_url)
        assert response.status_code == 201

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Insert link metadata
        payload = {"tmp_key": "tmp_value"}
        key = next(iter(payload))

        api_url = KYTOS_API + '/topology/v3/links/%s/metadata' % link_id1
        response = requests.post(api_url, data=json.dumps(payload), headers={'Content-type': 'application/json'})
        assert response.status_code == 201

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Verify that the metadata is inserted
        api_url = KYTOS_API + '/topology/v3/links/%s/metadata' % link_id1
        response = requests.get(api_url)
        data = response.json()
        keys = data['metadata'].keys()
        assert key in keys

        # Delete the link metadata
        api_url = KYTOS_API + '/topology/v3/links/%s/metadata/%s' % (link_id1, key)
        response = requests.delete(api_url)
        assert response.status_code == 200

        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=False, enable_all=False)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

        # Make sure the metadata is removed
        api_url = KYTOS_API + '/topology/v3/links/%s/metadata' % link_id1
        response = requests.get(api_url)
        data = response.json()

        keys = data['metadata'].keys()
        assert key not in keys

    def test_200_switch_disabled_on_clean_start(self):

        switch_id = "00:00:00:00:00:00:00:01"

        # Make sure the switch is disabled
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)
        data = response.json()

        assert response.status_code == 200
        assert data['switches'][switch_id]['enabled'] is False

    def test_300_interfaces_disabled_on_clean_start(self):

        # Make sure the interfaces are disabled
        api_url = KYTOS_API + '/topology/v3/interfaces'
        response = requests.get(api_url)
        data = response.json()
        for interface in data['interfaces']:
            assert data['interfaces'][interface]['enabled'] is False

    def test_400_switch_enabled_on_clean_start(self):

        # Start the controller setting an environment in
        # which all elements are disabled in a clean setting
        self.net.start_controller(clean_config=True, enable_all=True)
        self.net.wait_switches_connect()
        time.sleep(5)

        # Make sure the switch is disabled
        api_url = KYTOS_API + '/topology/v3/switches'
        response = requests.get(api_url)

        assert response.status_code == 200
        data = response.json()
        for switch in data['switches']:
            assert data['switches'][switch]['enabled'] is True

    def test_500_interfaces_enabled_on_clean_start(self):

        # Start the controller setting an environment in
        # which all elements are disabled in a clean setting
        self.net.start_controller(clean_config=True, enable_all=True)
        self.net.wait_switches_connect()
        time.sleep(5)

        # Make sure the interfaces are disabled
        api_url = KYTOS_API + '/topology/v3/interfaces'
        response = requests.get(api_url)

        assert response.status_code == 200
        data = response.json()
        for interface in data['interfaces']:
            assert data['interfaces'][interface]['enabled'] is True
