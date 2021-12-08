import time

import pytest
import requests

from tests.helpers import NetworkTest

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % CONTROLLER

class TestE2EMefEline:
    net = None

    def setup_method(self, method):
        """
        It is called at the beginning of every class method execution
        """
        # Since some tests may set a link to down state, we should reset
        # the link state to up (for all links)
        self.net.config_all_links_up()
        # Start the controller setting an environment in
        # which all elements are disabled in a clean setting
        self.net.start_controller(clean_config=True, enable_all=True)
        self.net.wait_switches_connect()
        time.sleep(10)

    @classmethod
    def setup_class(cls):
        cls.net = NetworkTest(CONTROLLER, topo_name='amlight')
        cls.net.start()
        cls.net.restart_kytos_clean()
        cls.net.wait_switches_connect()
        time.sleep(5)

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def restart(self, _clean_config=False, _enable_all=True):
        # Start the controller setting an environment in which the setting is
        # preserved (persistence) and avoid the default enabling of all elements
        self.net.start_controller(clean_config=_clean_config, enable_all=_enable_all)
        self.net.wait_switches_connect()

        # Wait a few seconds to kytos execute LLDP
        time.sleep(10)

    def create_evc(self, uni_a="00:00:00:00:00:00:00:01:1", uni_z="00:00:00:00:00:00:00:02:1", vlan_id=100):
        payload = {
            "name": "Vlan_%s" % vlan_id,
            "enabled": True,
            "dynamic_backup_path": True,
            "uni_a": {
                "interface_id": uni_a,
                "tag": {"tag_type": 1, "value": vlan_id}
            },
            "uni_z": {
                "interface_id": uni_z,
                "tag": {"tag_type": 1, "value": vlan_id}
            }
        }
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        response = requests.post(api_url, json=payload)
        data = response.json()
        return data['circuit_id']

    #
    # Issue: https://github.com/kytos-ng/mef_eline/issues/72
    #
    @pytest.mark.xfail
    def test_005_create_evc_on_nni(self):
        """Test to evaluate how mef_eline will behave when the uni is actually
        an NNI."""
        api_url = KYTOS_API + '/mef_eline/v2/evc/'
        evc1 = self.create_evc(uni_a='00:00:00:00:00:00:00:16:5',
                               uni_z='00:00:00:00:00:00:00:11:1',
                               vlan_id=100)

        time.sleep(10)

        # It verifies EVC's data
        response = requests.get(api_url + evc1)
        data = response.json()
        assert data['enabled'] == True
        assert data['active'] == True

        # Verify connectivity
        h6, h1 = self.net.net.get('h6', 'h1')
        h6.cmd('ip link add link %s name vlan100 type vlan id 100' % (h6.intfNames()[0]))
        h6.cmd('ip link set up vlan100')
        h6.cmd('ip addr add 10.1.0.6/24 dev vlan100')
        h1.cmd('ip link add link %s name vlan100 type vlan id 100' % (h1.intfNames()[0]))
        h1.cmd('ip link set up vlan100')
        h1.cmd('ip addr add 10.1.0.1/24 dev vlan100')

        result = h6.cmd('ping -c1 10.1.0.1')
        assert ', 0% packet loss,' in result

        # clean up
        h6.cmd('ip link del vlan100')
        h1.cmd('ip link del vlan100')
