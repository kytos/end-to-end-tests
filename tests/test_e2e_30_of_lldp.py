import unittest
import requests
from tests.helpers import NetworkTest
import os
import time
import json

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % (CONTROLLER)


class TestE2EOfLLDP(unittest.TestCase):
    net = None

    @classmethod
    def setUpClass(cls):
        cls.net = NetworkTest(CONTROLLER)
        cls.net.start()
        cls.net.restart_kytos_clean()

    @classmethod
    def tearDownClass(cls):
        cls.net.stop()

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
                "00:00:00:00:00:00:00:01:1","00:00:00:00:00:00:00:01:2","00:00:00:00:00:00:00:01:3", "00:00:00:00:00:00:00:01:4", "00:00:00:00:00:00:00:01:4294967294",
                "00:00:00:00:00:00:00:02:1","00:00:00:00:00:00:00:02:2","00:00:00:00:00:00:00:02:3", "00:00:00:00:00:00:00:02:4294967294",
                "00:00:00:00:00:00:00:03:1","00:00:00:00:00:00:00:03:2","00:00:00:00:00:00:00:03:3", "00:00:00:00:00:00:00:03:4294967294"
        ]
        assert set(data["interfaces"]) == set(expected_interfaces)

