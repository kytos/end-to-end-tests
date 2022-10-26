import os
import json
import time
import base64
import shutil
import requests
from tests.helpers import NetworkTest
from kytos.core.auth import UserController

CONTROLLER = '127.0.0.1'
KYTOS_API = 'http://%s:8181/api/kytos' % CONTROLLER


class TestE2EKytosAuth:
    net = None

    def setup_method(self, method):
        """
        It is called at the beginning of every class method execution
        """
        self.net.start_controller(clean_config=True, enable_all=False)
        self.user_data = {
            "username": os.environ.get("USER_USERNAME"),
            "password": os.environ.get("USER_PASSWORD"),
            "email": os.environ.get("USER_EMAIL")
        }
        self.user_controller = UserController()
        self.user_controller.create_user(self.user_data)
        self.token = self.get_token()
        time.sleep(5)

    @classmethod
    def setup_class(cls):
        cls.net = NetworkTest(CONTROLLER)
        cls.net.start()
        # rotate logfile (copy/truncate strategy)
        logfile = '/var/log/syslog'
        shutil.copy(logfile, logfile + '-' + time.strftime("%Y%m%d%H%M%S"))
        open(logfile, 'w').close()

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def get_token(self):
        api_url = KYTOS_API + '/core/auth/login/'
        username = os.environ.get("USER_USERNAME")
        password = os.environ.get("USER_PASSWORD")

        header = {
            "Authorization": "Basic "
            + base64.b64encode(
                bytes(username + ":" + password, "ascii")
            ).decode("ascii")
        }
        answer = requests.get(api_url, headers=header, auth=(username, password))

        return answer.json()['token']


    def test_authenticate_user(self):
        api_url = KYTOS_API + '/core/auth/login/'
        username = os.environ.get("USER_USERNAME")
        password = os.environ.get("USER_PASSWORD")
        header = {
            "Authorization": "Basic "
            + base64.b64encode(
                bytes(username + ":" + password, "ascii")
            ).decode("ascii")
        }
        answer = requests.get(api_url, headers=header, auth=(username, password))
        assert answer.status_code == 200

    def test_list_users(self):
        auth_header = {"Authorization": f"Bearer {self.token}"}
        api_url = KYTOS_API + '/core/auth/users/'
        answer = requests.get(api_url, headers=auth_header)
        data = answer.json()["users"]
        assert list == type(data)
        assert os.environ.get("USER_USERNAME") == data[0]["username"]
        assert os.environ.get("USER_EMAIL") == data[0]["email"]

    def test_list_user(self):
        auth_header = {"Authorization": f"Bearer {self.token}"}
        username = os.environ.get("USER_USERNAME")
        api_url = KYTOS_API + '/core/auth/users/' + username
        answer = requests.get(api_url, headers=auth_header)
        data = answer.json()
        assert os.environ.get("USER_USERNAME") == data["username"]
        assert os.environ.get("USER_EMAIL") == data["email"]

    def test_create_user(self):
        auth_header = {"Authorization": f"Bearer {self.token}"}
        api_url = KYTOS_API + '/core/auth/users/'
        user_sc = {
            "username": "Seconduser",
            "password": "SecondUser123",
            "email": "second@kytos.io"
        }
        answer = requests.post(api_url, json=user_sc, headers=auth_header)
        assert answer.status_code == 201

    def test_delete_user(self):
        auth_header = {"Authorization": f"Bearer {self.token}"}
        username = os.environ.get("USER_USERNAME")
        api_url = KYTOS_API + '/core/auth/users/' + username
        answer = requests.delete(api_url, headers=auth_header)
        assert answer.status_code == 200

    def test_update_user(self): # PATCH
        auth_header = {"Authorization": f"Bearer {self.token}"}
        username = os.environ.get("USER_USERNAME")
        email = {"email": "changed@kytos.io"}
        api_url = KYTOS_API + '/core/auth/users/' + username
        answer = requests.patch(api_url, json=email, headers=auth_header)
        assert answer.status_code == 200
