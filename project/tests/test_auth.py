import os
import sys
import unittest
import tempfile
import shutil

# Set up paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config

# Use a temp directory for test database and storage
_test_dir = tempfile.mkdtemp()
Config.DATABASE_PATH = os.path.join(_test_dir, "test.db")
Config.STORAGE_PATH = os.path.join(_test_dir, "storage")
Config.ENCRYPTION_KEY_FILE = os.path.join(_test_dir, "test.key")

from app.auth.authentication import AuthenticationService
from app.auth.two_factor import TwoFactorAuth
from app.models.database import init_db


class TestAuthentication(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def test_validate_username_valid(self):
        valid, _ = AuthenticationService.validate_username("testuser")
        self.assertTrue(valid)

    def test_validate_username_too_short(self):
        valid, msg = AuthenticationService.validate_username("ab")
        self.assertFalse(valid)
        self.assertIn("3-30", msg)

    def test_validate_username_special_chars(self):
        valid, _ = AuthenticationService.validate_username("user@name")
        self.assertFalse(valid)

    def test_validate_password_valid(self):
        valid, _ = AuthenticationService.validate_password("Str0ng!Pass")
        self.assertTrue(valid)

    def test_validate_password_too_short(self):
        valid, msg = AuthenticationService.validate_password("Sh0rt!")
        self.assertFalse(valid)

    def test_validate_password_no_uppercase(self):
        valid, _ = AuthenticationService.validate_password("lowercase1!")
        self.assertFalse(valid)

    def test_validate_password_no_digit(self):
        valid, _ = AuthenticationService.validate_password("NoDigits!here")
        self.assertFalse(valid)

    def test_validate_password_no_special(self):
        valid, _ = AuthenticationService.validate_password("NoSpecial1x")
        self.assertFalse(valid)

    def test_hash_and_verify_password(self):
        pw = "TestPass123!"
        hashed = AuthenticationService.hash_password(pw)
        self.assertTrue(AuthenticationService.verify_password(pw, hashed))
        self.assertFalse(AuthenticationService.verify_password("wrong", hashed))

    def test_register_success(self):
        user, msg = AuthenticationService.register("auth_test_user", "Str0ng!Pass")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "auth_test_user")

    def test_register_duplicate(self):
        AuthenticationService.register("dup_user", "Str0ng!Pass")
        user, msg = AuthenticationService.register("dup_user", "Str0ng!Pass")
        self.assertIsNone(user)
        self.assertIn("already exists", msg)

    def test_register_duplicate_case_insensitive(self):
        AuthenticationService.register("CaseUser", "Str0ng!Pass")
        user, msg = AuthenticationService.register("caseuser", "Str0ng!Pass")
        self.assertIsNone(user)
        self.assertIn("already exists", msg)

    def test_login_success(self):
        AuthenticationService.register("login_user", "Str0ng!Pass")
        user, msg = AuthenticationService.login("login_user", "Str0ng!Pass")
        self.assertIsNotNone(user)
        self.assertEqual(msg, "Login successful.")

    def test_login_wrong_password(self):
        AuthenticationService.register("login_fail_user", "Str0ng!Pass")
        user, msg = AuthenticationService.login("login_fail_user", "WrongPass1!")
        self.assertIsNone(user)
        self.assertIn("Invalid", msg)

    def test_login_nonexistent_user(self):
        user, msg = AuthenticationService.login("nobody", "Pass123!")
        self.assertIsNone(user)

    def test_pin_lock_enable_and_verify(self):
        user, _ = AuthenticationService.register("pin_user", "Str0ng!Pass")

        result, message = TwoFactorAuth.setup_2fa(user.id, "123456")
        self.assertIsNotNone(result)
        self.assertIn("enabled", message.lower())

        success, verify_message = TwoFactorAuth.verify_otp(user.id, "123456")
        self.assertTrue(success)
        self.assertIn("verified", verify_message.lower())

    def test_pin_lock_enable_rejects_invalid_pins(self):
        user, _ = AuthenticationService.register("pin_invalid_user", "Str0ng!Pass")

        for invalid_pin in ["", "12345", "1234567", "12ab56", " 123456 "]:
            result, message = TwoFactorAuth.setup_2fa(user.id, invalid_pin)
            self.assertIsNone(result)
            self.assertIn("exactly 6 digits", message.lower())

    def test_login_requires_pin_when_enabled(self):
        user, _ = AuthenticationService.register("pin_login_user", "Str0ng!Pass")
        TwoFactorAuth.setup_2fa(user.id, "654321")

        user_obj, message = AuthenticationService.login("pin_login_user", "Str0ng!Pass")
        self.assertIsNotNone(user_obj)
        self.assertEqual(message, "PIN_REQUIRED")

    @classmethod
    def tearDownClass(cls):
        pass


if __name__ == '__main__':
    unittest.main()
