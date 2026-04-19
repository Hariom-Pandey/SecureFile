import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config

_test_dir = tempfile.mkdtemp()
Config.DATABASE_PATH = os.path.join(_test_dir, "test_pending.db")
Config.STORAGE_PATH = os.path.join(_test_dir, "storage")
Config.ENCRYPTION_KEY_FILE = os.path.join(_test_dir, "test_pending.key")

from main import create_app
from app.protection.encryption import EncryptionService


class TestPendingSecondStepTokenRestrictions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        EncryptionService.reset()
        cls.app = create_app(testing=True)
        cls.client = cls.app.test_client()

    def _register_and_login(self, username, password):
        register_resp = self.client.post(
            '/api/auth/register',
            json={"username": username, "password": password}
        )
        self.assertEqual(register_resp.status_code, 201)

        login_resp = self.client.post(
            '/api/auth/login',
            json={"username": username, "password": password}
        )
        self.assertEqual(login_resp.status_code, 200)
        token = login_resp.get_json()["access_token"]
        return token

    def test_pending_token_cannot_access_protected_endpoints(self):
        username = "pending_user"
        password = "Str0ng!Pass"
        access_token = self._register_and_login(username, password)

        upload_resp = self.client.post(
            '/api/files/upload',
            headers={"Authorization": f"Bearer {access_token}"},
            data={"file": (io.BytesIO(b"hello"), "hello.txt")},
            content_type='multipart/form-data'
        )
        self.assertEqual(upload_resp.status_code, 201)
        file_id = upload_resp.get_json()["file"]["id"]

        setup_resp = self.client.post(
            '/api/auth/setup-2fa',
            headers={"Authorization": f"Bearer {access_token}"},
            json={"pin_code": "123456"}
        )
        self.assertEqual(setup_resp.status_code, 200)

        pending_login = self.client.post(
            '/api/auth/login',
            json={"username": username, "password": password}
        )
        self.assertEqual(pending_login.status_code, 200)
        pending_body = pending_login.get_json()
        self.assertTrue(pending_body.get("requires_2fa"))
        temp_token = pending_body["temp_token"]

        me_resp = self.client.get(
            '/api/auth/me',
            headers={"Authorization": f"Bearer {temp_token}"}
        )
        self.assertEqual(me_resp.status_code, 403)

        files_resp = self.client.get(
            '/api/files/',
            headers={"Authorization": f"Bearer {temp_token}"}
        )
        self.assertEqual(files_resp.status_code, 403)

        preview_resp = self.client.get(
            f'/api/files/{file_id}/preview?token={temp_token}'
        )
        self.assertEqual(preview_resp.status_code, 403)

    def test_pending_token_becomes_full_after_pin_verify(self):
        username = "pending_user2"
        password = "Str0ng!Pass"
        access_token = self._register_and_login(username, password)

        setup_resp = self.client.post(
            '/api/auth/setup-2fa',
            headers={"Authorization": f"Bearer {access_token}"},
            json={"pin_code": "654321"}
        )
        self.assertEqual(setup_resp.status_code, 200)

        pending_login = self.client.post(
            '/api/auth/login',
            json={"username": username, "password": password}
        )
        temp_token = pending_login.get_json()["temp_token"]

        verify_resp = self.client.post(
            '/api/auth/verify-2fa',
            headers={"Authorization": f"Bearer {temp_token}"},
            json={"pin_code": "654321"}
        )
        self.assertEqual(verify_resp.status_code, 200)
        full_token = verify_resp.get_json()["access_token"]

        me_resp = self.client.get(
            '/api/auth/me',
            headers={"Authorization": f"Bearer {full_token}"}
        )
        self.assertEqual(me_resp.status_code, 200)


if __name__ == '__main__':
    unittest.main()
