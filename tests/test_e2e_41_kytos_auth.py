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
        self.username = "Superuser"
        self.password = "Password123"
        self.email = "user@kytos.io"
        self.user_controller = UserController()
        self.user_controller.create_user({
            "username": self.username,
            "password": self.password,
            "email": self.email
        })
        self.token = self.get_token()
        self.auth_header = {"Authorization": f"Bearer {self.token}"}
        time.sleep(5)

    @classmethod
    def setup_class(cls):
        cls.net = NetworkTest(CONTROLLER)
        cls.net.start()

    @classmethod
    def teardown_class(cls):
        cls.net.stop()

    def get_token(self):
        api_url = KYTOS_API + '/core/auth/login/'
        answer = requests.get(api_url, auth=(self.username, self.password))

        return answer.json()['token']

    def test_authenticate_user(self):
        api_url = KYTOS_API + '/core/auth/login/'
        answer = requests.get(api_url, auth=(self.username, self.password))
        assert answer.status_code == 200

        #Error: Unauthorized
        wrong_password = "wrong_password"
        answer_fail = requests.get(api_url, auth=(self.username, wrong_password))
        assert answer_fail.status_code == 401
        assert answer_fail.json()["description"] == "Incorrect password"

        #Error: NoTFound
        wrong_username = "wrong_username"
        fail_answer = requests.get(api_url, auth=(wrong_username, self.password))
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
        assert self.username == data[0]["username"]
        assert self.email == data[0]["email"]
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
        api_url = KYTOS_API + '/core/auth/users/' + self.username
        answer = requests.get(api_url, headers=self.auth_header)
        data = answer.json()
        assert self.username == data["username"]
        assert self.email == data["email"]

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
        api_url = KYTOS_API + '/core/auth/users/' + self.username
        answer = requests.delete(api_url, headers=self.auth_header)
        assert answer.status_code == 200
        assert answer.json() == f"User {self.username} deleted succesfully"
        new_data = self.user_controller.get_user(self.username)
        assert new_data["deleted_at"] is not None
        assert new_data["state"] == "inactive"

        #Error: NotFound
        api_url = KYTOS_API + '/core/auth/users/' + "non_exist"
        answer = requests.delete(api_url, headers=self.auth_header)
        assert answer.status_code == 404

    def test_update_user_username(self):
        api_url = KYTOS_API + '/core/auth/users/' + self.username
        new_username = {"username": "NewUsername"}
        answer = requests.patch(api_url, json=new_username,
                                headers=self.auth_header)
        assert answer.status_code == 200

        api_url = KYTOS_API + '/core/auth/login/'
        new_answer = requests.get(api_url, auth=(new_username["username"], self.password))
        assert new_answer.status_code == 200

    def test_update_user_password(self):
        api_url = KYTOS_API + '/core/auth/users/' + self.username
        new_password = {"password": "NewPassword456"}
        answer = requests.patch(api_url, json=new_password,
                                headers=self.auth_header)
        assert answer.status_code == 200

        api_url = KYTOS_API + '/core/auth/login/'
        answer = requests.get(api_url, auth=(self.username, new_password["password"]))
        assert answer.status_code == 200

    def test_update_user_email(self):
        new_email = {"email": "changed@kytos.io"}
        api_url = KYTOS_API + '/core/auth/users/' + self.username
        answer = requests.patch(api_url, json=new_email,
                                headers=self.auth_header)
        assert answer.status_code == 200
        updated_data = self.user_controller.get_user(self.username)
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
