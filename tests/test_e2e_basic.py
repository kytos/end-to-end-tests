import unittest
import requests
from tests.helpers import NetworkTest

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % (CONTROLLER)


class TestE2EBasic(unittest.TestCase):
    def setUp(self):
        self.net = NetworkTest(CONTROLLER)
        self.net.start()

    def tearDown(self):
        # This function tears down the whole topology.
        self.net.stop()

    def test_list_without_circuits(self):
        """Test if list circuits return 'no circuit stored.'."""
        api_url = KYTOS_API+'/mef_eline/v2/evc/'
        response = requests.get(api_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})
