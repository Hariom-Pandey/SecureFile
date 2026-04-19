import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config

_test_dir = tempfile.mkdtemp()
Config.DATABASE_PATH = os.path.join(_test_dir, "test_ac.db")
Config.STORAGE_PATH = os.path.join(_test_dir, "storage")
Config.ENCRYPTION_KEY_FILE = os.path.join(_test_dir, "test_ac.key")

from app.models.database import init_db
from app.auth.authentication import AuthenticationService
from app.protection.access_control import AccessControlService
from app.files.file_operations import FileOperations
from app.protection.encryption import EncryptionService


class TestAccessControl(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        EncryptionService.reset()
        init_db()

        cls.admin, _ = AuthenticationService.register("ac_admin", "Admin1!pass", "admin")
        cls.user1, _ = AuthenticationService.register("ac_user1", "User1!pass1")
        cls.user2, _ = AuthenticationService.register("ac_user2", "User2!pass2")
        cls.viewer, _ = AuthenticationService.register("ac_viewer", "Viewer1!pass", "viewer")

        # User1 uploads a file
        record, _ = FileOperations.upload_file(
            "test.txt", b"test content", cls.user1.id
        )
        cls.file_id = record.id

    def test_admin_can_read_any_file(self):
        self.assertTrue(
            AccessControlService.can_read_file(self.admin.id, self.file_id)
        )

    def test_owner_can_read_own_file(self):
        self.assertTrue(
            AccessControlService.can_read_file(self.user1.id, self.file_id)
        )

    def test_other_user_cannot_read_file(self):
        self.assertFalse(
            AccessControlService.can_read_file(self.user2.id, self.file_id)
        )

    def test_share_read_permission(self):
        success, _ = AccessControlService.share_file(
            self.file_id, self.user2.id, "read", self.user1.id
        )
        self.assertTrue(success)
        self.assertTrue(
            AccessControlService.can_read_file(self.user2.id, self.file_id)
        )
        # Read permission doesn't grant write
        self.assertFalse(
            AccessControlService.can_write_file(self.user2.id, self.file_id)
        )

    def test_share_write_permission(self):
        success, _ = AccessControlService.share_file(
            self.file_id, self.user2.id, "write", self.user1.id
        )
        self.assertTrue(success)
        self.assertTrue(
            AccessControlService.can_write_file(self.user2.id, self.file_id)
        )

    def test_non_owner_cannot_share(self):
        success, msg = AccessControlService.share_file(
            self.file_id, self.viewer.id, "read", self.user2.id
        )
        self.assertFalse(success)
        self.assertIn("permission", msg.lower())

    def test_revoke_access(self):
        AccessControlService.share_file(
            self.file_id, self.viewer.id, "read", self.user1.id
        )
        self.assertTrue(
            AccessControlService.can_read_file(self.viewer.id, self.file_id)
        )

        AccessControlService.revoke_access(
            self.file_id, self.viewer.id, self.user1.id
        )
        self.assertFalse(
            AccessControlService.can_read_file(self.viewer.id, self.file_id)
        )

    def test_role_check(self):
        self.assertTrue(AccessControlService.is_admin(self.admin.id))
        self.assertFalse(AccessControlService.is_admin(self.user1.id))

    def test_viewer_rbac_boundaries_are_enforced(self):
        # Viewer can read when explicitly shared.
        ok, _ = AccessControlService.share_file(
            self.file_id, self.viewer.id, "read", self.user1.id
        )
        self.assertTrue(ok)
        self.assertTrue(AccessControlService.can_read_file(self.viewer.id, self.file_id))

        # Viewer cannot escalate to write/delete/share/upload actions.
        self.assertFalse(AccessControlService.can_write_file(self.viewer.id, self.file_id))
        self.assertFalse(AccessControlService.can_delete_file(self.viewer.id, self.file_id))
        self.assertFalse(AccessControlService.can_share_file(self.viewer.id, self.file_id))
        self.assertFalse(AccessControlService.can_upload_file(self.viewer.id))


if __name__ == '__main__':
    unittest.main()
