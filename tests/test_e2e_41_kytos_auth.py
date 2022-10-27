import os
import time
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
        self.auth_header = {"Authorization": f"Bearer {self.token}"}
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
        answer = requests.get(api_url, auth=(username, password))

        return answer.json()['token']

    def test_authenticate_user(self):
        api_url = KYTOS_API + '/core/auth/login/'
        username = os.environ.get("USER_USERNAME")
        password = os.environ.get("USER_PASSWORD")
        answer = requests.get(api_url, auth=(username, password))
        assert answer.status_code == 200

        #Error: Unauthorized
        username = os.environ.get("USER_USERNAME")
        wrong_password = "wrong_password"
        answer_fail = requests.get(api_url, auth=(username, wrong_password))
        assert answer_fail.status_code == 401
        assert answer_fail.json()["description"] == "Incorrect password"

        #Error: NoTFound
        wrong_username = "wrong_username"
        password = os.environ.get("USER_PASSWORD")
        fail_answer = requests.get(api_url, auth=(wrong_username, password))
        assert fail_answer.status_code == 404
        assert fail_answer.json()["description"] == f"User {wrong_username} not found"

    def test_list_users(self):
        new_data = {
            "username": "New_user",
            "password": "New_user_123",
            "email": "new@kytos.io"
        }
        self.user_controller.create_user(new_data)
        api_url = KYTOS_API + '/core/auth/users/'
        answer = requests.get(api_url, headers=self.auth_header)
        data = answer.json()["users"]
        assert len(data) > 1
        assert list == type(data)
        assert os.environ.get("USER_USERNAME") == data[0]["username"]
        assert os.environ.get("USER_EMAIL") == data[0]["email"]
        assert new_data["username"] == data[1]["username"]
        assert new_data["email"] == data[1]["email"]
        for user in data:
            assert user["state"] == "active"
            assert user["updated_at"] is not None
            assert user["inserted_at"] is not None
            assert user["deleted_at"] is None

        #Error: "Token not sent"
        wrong_header = {"Authorization": "Bearer wrong"}
        answer_fail = requests.get(api_url, headers=wrong_header)
        assert answer_fail.status_code == 401

    def test_list_user(self):
        username = os.environ.get("USER_USERNAME")
        api_url = KYTOS_API + '/core/auth/users/' + username
        answer = requests.get(api_url, headers=self.auth_header)
        data = answer.json()
        assert os.environ.get("USER_USERNAME") == data["username"]
        assert os.environ.get("USER_EMAIL") == data["email"]

        #Error: NotFound
        api_url = KYTOS_API + '/core/auth/users/' + "non_exist"
        answer_fail = requests.get(api_url, headers=self.auth_header)
        assert answer_fail.status_code == 404

    def test_create_user(self):
        api_url = KYTOS_API + '/core/auth/users/'
        user_data = {
            "username": "Seconduser",
            "password": "SecondUser123",
            "email": "second@kytos.io"
        }
        answer = requests.post(api_url, json=user_data,
                               headers=self.auth_header)
        assert answer.status_code == 201
        assert answer.json() == "User successfully created"
        user = self.user_controller.get_user(user_data["username"])
        assert user["state"] == "active"
        assert user["email"] == user_data["email"]
        
        #Error: DuplicateKeyError - Conflict
        fail_answer = requests.post(api_url, json=user_data,
                                    headers=self.auth_header)
        assert fail_answer.status_code == 409

        wrong_data = {
            "username": "wronguser",
            "password": "wrongpassword",
            "email": "wrong_email"
        }
        #Error: ValidationError - BadRequest
        answer_fail = requests.post(api_url, json=wrong_data,
                                    headers=self.auth_header)
        assert answer_fail.status_code == 400

    def test_delete_user(self):
        username = os.environ.get("USER_USERNAME")
        api_url = KYTOS_API + '/core/auth/users/' + username
        answer = requests.delete(api_url, headers=self.auth_header)
        assert answer.status_code == 200
        assert answer.json() == f"User {username} deleted succesfully"
        new_data = self.user_controller.get_user(username)
        assert new_data["deleted_at"] is not None
        assert new_data["state"] == "inactive"

        #Error: NotFound
        api_url = KYTOS_API + '/core/auth/users/' + "non_exist"
        answer = requests.delete(api_url, headers=self.auth_header)
        assert answer.status_code == 404

    def test_update_user_username(self):
        username = os.environ.get("USER_USERNAME")
        api_url = KYTOS_API + '/core/auth/users/' + username
        new_username = {"username": "NewUsername"}
        answer = requests.patch(api_url, json=new_username,
                                headers=self.auth_header)
        assert answer.status_code == 200

        api_url = KYTOS_API + '/core/auth/login/'
        password = os.environ.get("USER_PASSWORD")
        new_answer = requests.get(api_url, auth=(new_username["username"], password))
        assert new_answer.status_code == 200

    def test_update_user_password(self):
        username = os.environ.get("USER_USERNAME")
        api_url = KYTOS_API + '/core/auth/users/' + username
        new_password = {"password": "NewPassword456"}
        answer = requests.patch(api_url, json=new_password,
                                headers=self.auth_header)
        assert answer.status_code == 200

        api_url = KYTOS_API + '/core/auth/login/'
        answer = requests.get(api_url, auth=(username, new_password["password"]))
        assert answer.status_code == 200

    def test_update_user_email(self):
        username = os.environ.get("USER_USERNAME")
        new_email = {"email": "changed@kytos.io"}
        api_url = KYTOS_API + '/core/auth/users/' + username
        answer = requests.patch(api_url, json=new_email,
                                headers=self.auth_header)
        assert answer.status_code == 200
        updated_data = self.user_controller.get_user(username)
        assert updated_data["email"] == new_email["email"]

        #Error: NotFound
        api_url = KYTOS_API + '/core/auth/users/' + "non_exist"
        answer = requests.patch(api_url, json=new_email,
                                headers=self.auth_header)
        assert answer.status_code == 404

        #Error: ValidationError - BadRequest
        wrong_email = {"email": "wrong_email"}
        answer = requests.patch(api_url, json=wrong_email,
                                headers=self.auth_header)
        assert answer.status_code == 400
