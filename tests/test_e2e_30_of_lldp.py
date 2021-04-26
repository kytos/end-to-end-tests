import requests
from tests.helpers import NetworkTest
import time

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % CONTROLLER


class TestE2EOfLLDP:
    net = None

    @classmethod
    def setup_class(cls):
        cls.net = NetworkTest(CONTROLLER)
        cls.net.start()
        cls.net.restart_kytos_clean()
        cls.net.wait_switches_connect()
        time.sleep(10)

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def get_iface_stats_rx_pkt(self, host):
        rx_pkts = host.cmd("ip -s link show dev %s | grep RX: -A 1 | tail -n1 | awk '{print $2}'" % (host.intfNames()[0]))
        return int(rx_pkts.strip())

    @staticmethod
    def disable_all_of_lldp():
        api_url = KYTOS_API + '/of_lldp/v1/interfaces/'
        response = requests.get(api_url)
        data = response.json()
        all_interfaces = data.get("interfaces", [])
        response = requests.post(api_url+'disable/', json={"interfaces": all_interfaces})
        assert response.status_code == 200

    def test_001_list_interfaces_with_lldp(self):
        """ List interfaces with OF LLDP. """
        api_url = KYTOS_API + '/of_lldp/v1/interfaces/'
        response = requests.get(api_url)
        assert response.status_code == 200
        data = response.json()
        assert "interfaces" in data
        # the number of interfaces should match the topology + the OFP_LOCAL port, for the RingTopology it means:
        # mininet> net
        # ...
        # s1 lo:  s1-eth1:h11-eth0 s1-eth2:h12-eth0 s1-eth3:s2-eth2 s1-eth4:s3-eth3
        # s2 lo:  s2-eth1:h2-eth0 s2-eth2:s1-eth3 s2-eth3:s3-eth2
        # s3 lo:  s3-eth1:h3-eth0 s3-eth2:s2-eth3 s3-eth3:s1-eth4
        expected_interfaces = [
                "00:00:00:00:00:00:00:01:1", "00:00:00:00:00:00:00:01:2", "00:00:00:00:00:00:00:01:3",
                "00:00:00:00:00:00:00:01:4", "00:00:00:00:00:00:00:01:4294967294",
                "00:00:00:00:00:00:00:02:1", "00:00:00:00:00:00:00:02:2", "00:00:00:00:00:00:00:02:3",
                "00:00:00:00:00:00:00:02:4294967294",
                "00:00:00:00:00:00:00:03:1", "00:00:00:00:00:00:00:03:2", "00:00:00:00:00:00:00:03:3",
                "00:00:00:00:00:00:00:03:4294967294"
        ]
        assert set(data["interfaces"]) == set(expected_interfaces)

        # make sure the interfaces are actually receiving LLDP
        h11, h12, h2, h3 = self.net.net.get('h11', 'h12', 'h2', 'h3')
        rx_stats_h11 = self.get_iface_stats_rx_pkt(h11)
        rx_stats_h12 = self.get_iface_stats_rx_pkt(h12)
        rx_stats_h2 = self.get_iface_stats_rx_pkt(h2)
        rx_stats_h3 = self.get_iface_stats_rx_pkt(h3)
        time.sleep(10)
        rx_stats_h11_2 = self.get_iface_stats_rx_pkt(h11)
        rx_stats_h12_2 = self.get_iface_stats_rx_pkt(h12)
        rx_stats_h2_2 = self.get_iface_stats_rx_pkt(h2)
        rx_stats_h3_2 = self.get_iface_stats_rx_pkt(h3)

        assert rx_stats_h11_2 > rx_stats_h11 \
            and rx_stats_h12_2 > rx_stats_h12 \
            and rx_stats_h2_2 > rx_stats_h2 \
            and rx_stats_h3_2 > rx_stats_h3

    def test_010_disable_of_lldp(self):
        """ Test if the disabling OF LLDP in an interface worked properly. """
        self.net.restart_kytos_clean()
        # disabling all the UNI interfaces
        payload = {
            "interfaces": [
                "00:00:00:00:00:00:00:01:1", "00:00:00:00:00:00:00:01:2", "00:00:00:00:00:00:00:01:4294967294",
                "00:00:00:00:00:00:00:02:1", "00:00:00:00:00:00:00:02:4294967294",
                "00:00:00:00:00:00:00:03:1", "00:00:00:00:00:00:00:03:4294967294"
            ]
        }
        expected_interfaces = [
                "00:00:00:00:00:00:00:01:3", "00:00:00:00:00:00:00:01:4",
                "00:00:00:00:00:00:00:02:2", "00:00:00:00:00:00:00:02:3",
                "00:00:00:00:00:00:00:03:2", "00:00:00:00:00:00:00:03:3"
        ]

        api_url = KYTOS_API + '/of_lldp/v1/interfaces/disable/'
        response = requests.post(api_url, json=payload)
        assert response.status_code == 200

        api_url = KYTOS_API + '/of_lldp/v1/interfaces/'
        response = requests.get(api_url)
        data = response.json()
        assert set(data["interfaces"]) == set(expected_interfaces)

        h11, h12, h2, h3 = self.net.net.get('h11', 'h12', 'h2', 'h3')
        rx_stats_h11 = self.get_iface_stats_rx_pkt(h11)
        rx_stats_h12 = self.get_iface_stats_rx_pkt(h12)
        rx_stats_h2 = self.get_iface_stats_rx_pkt(h2)
        rx_stats_h3 = self.get_iface_stats_rx_pkt(h3)
        time.sleep(10)
        rx_stats_h11_2 = self.get_iface_stats_rx_pkt(h11)
        rx_stats_h12_2 = self.get_iface_stats_rx_pkt(h12)
        rx_stats_h2_2 = self.get_iface_stats_rx_pkt(h2)
        rx_stats_h3_2 = self.get_iface_stats_rx_pkt(h3)

        assert rx_stats_h11_2 == rx_stats_h11 \
            and rx_stats_h12_2 == rx_stats_h12 \
            and rx_stats_h2_2 == rx_stats_h2 \
            and rx_stats_h3_2 == rx_stats_h3

        # restart kytos and check if lldp remains disabled
        self.net.start_controller(clean_config=False)
        self.net.wait_switches_connect()
        time.sleep(5)

        api_url = KYTOS_API + '/of_lldp/v1/interfaces/'
        response = requests.get(api_url)
        data = response.json()
        assert set(data["interfaces"]) == set(expected_interfaces)

    def test_020_enable_of_lldp(self):
        """ Test if enabling OF LLDP in an interface works properly. """
        self.net.restart_kytos_clean()
        time.sleep(5)
        TestE2EOfLLDP.disable_all_of_lldp()

        payload = {
            "interfaces": [
                "00:00:00:00:00:00:00:01:1"
            ]
        }
        expected_interfaces = [
                "00:00:00:00:00:00:00:01:1"
        ]

        api_url = KYTOS_API + '/of_lldp/v1/interfaces/enable/'
        response = requests.post(api_url, json=payload)
        assert response.status_code == 200

        api_url = KYTOS_API + '/of_lldp/v1/interfaces/'
        response = requests.get(api_url)
        data = response.json()
        assert set(data["interfaces"]) == set(expected_interfaces)

        h11 = self.net.net.get('h11')
        rx_stats_h11 = self.get_iface_stats_rx_pkt(h11)
        time.sleep(10)
        rx_stats_h11_2 = self.get_iface_stats_rx_pkt(h11)

        assert rx_stats_h11_2 > rx_stats_h11

        # restart kytos and check if lldp remains disabled
        self.net.start_controller(clean_config=False)
        self.net.wait_switches_connect()
        time.sleep(5)

        api_url = KYTOS_API + '/of_lldp/v1/interfaces/'
        response = requests.get(api_url)
        data = response.json()
        assert set(data["interfaces"]) == set(expected_interfaces)

    def test_030_change_polling_interval(self):
        """ Test if changing the polling interval works works properly. """
        self.net.restart_kytos_clean()

        api_url = KYTOS_API + '/of_lldp/v1/polling_time'
        response = requests.get(api_url)
        assert response.status_code == 200
        data = response.json()
        assert "polling_time" in data
        assert data["polling_time"] == 3

        h11 = self.net.net.get('h11')
        rx_stats_h11 = self.get_iface_stats_rx_pkt(h11)
        lldp_wait = 31
        time.sleep(lldp_wait)
        rx_stats_h11_2 = self.get_iface_stats_rx_pkt(h11)

        # the delta pps should be around 10, because the interface is every 3s
        delta_pps = rx_stats_h11_2 - rx_stats_h11

        api_url = KYTOS_API + '/of_lldp/v1/polling_time'
        response = requests.post(api_url, json={"polling_time": 1})
        assert response.status_code == 200

        response = requests.get(api_url)
        data = response.json()
        assert data["polling_time"] == 1

        rx_stats_h11 = self.get_iface_stats_rx_pkt(h11)
        time.sleep(lldp_wait)
        rx_stats_h11_2 = self.get_iface_stats_rx_pkt(h11)

        delta_pps_2 = rx_stats_h11_2 - rx_stats_h11

        # the delta pps now should be around 30, because the interval is every 1s
        assert delta_pps_2 > delta_pps + 15
