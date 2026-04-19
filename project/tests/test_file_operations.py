import os
import sys
import unittest
import tempfile
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config

_test_dir = tempfile.mkdtemp()
Config.DATABASE_PATH = os.path.join(_test_dir, "test_files.db")
Config.STORAGE_PATH = os.path.join(_test_dir, "storage")
Config.ENCRYPTION_KEY_FILE = os.path.join(_test_dir, "test_files.key")

from app.models.database import init_db
from app.auth.authentication import AuthenticationService
from app.files.file_operations import FileOperations
from app.protection.encryption import EncryptionService


class TestFileOperations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        EncryptionService.reset()
        init_db()

        cls.user1, _ = AuthenticationService.register("file_user1", "FileUser1!")
        cls.user2, _ = AuthenticationService.register("file_user2", "FileUser2!")

    def test_upload_file(self):
        record, messages = FileOperations.upload_file(
            "hello.txt", b"Hello world!", self.user1.id
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.original_name, "hello.txt")
        self.assertEqual(record.file_size, 12)

    def test_upload_blocked_extension(self):
        record, messages = FileOperations.upload_file(
            "virus.exe", b"data", self.user1.id
        )
        self.assertIsNone(record)

    def test_read_file(self):
        record, _ = FileOperations.upload_file(
            "readme.txt", b"Read me!", self.user1.id
        )
        result, msg = FileOperations.read_file(record.id, self.user1.id)
        self.assertIsNotNone(result)
        self.assertEqual(result["data"], b"Read me!")

    def test_read_file_access_denied(self):
        record, _ = FileOperations.upload_file(
            "private.txt", b"Secret", self.user1.id
        )
        result, msg = FileOperations.read_file(record.id, self.user2.id)
        self.assertIsNone(result)
        self.assertIn("denied", msg.lower())

    def test_write_file(self):
        record, _ = FileOperations.upload_file(
            "edit.txt", b"Original", self.user1.id
        )
        success, _ = FileOperations.write_file(
            record.id, b"Updated content", self.user1.id
        )
        self.assertTrue(success)

        result, _ = FileOperations.read_file(record.id, self.user1.id)
        self.assertEqual(result["data"], b"Updated content")

    def test_delete_file(self):
        record, _ = FileOperations.upload_file(
            "delete_me.txt", b"To delete", self.user1.id
        )
        success, _ = FileOperations.delete_file(record.id, self.user1.id)
        self.assertTrue(success)

        result, _ = FileOperations.read_file(record.id, self.user1.id)
        self.assertIsNone(result)

    def test_share_and_read(self):
        record, _ = FileOperations.upload_file(
            "shared.txt", b"Shared content", self.user1.id
        )
        # User2 can't read yet
        result, _ = FileOperations.read_file(record.id, self.user2.id)
        self.assertIsNone(result)

        # Share with user2
        success, _ = FileOperations.share_file(
            record.id, "file_user2", "read", self.user1.id
        )
        self.assertTrue(success)

        # Now user2 can read
        result, _ = FileOperations.read_file(record.id, self.user2.id)
        self.assertIsNotNone(result)
        self.assertEqual(result["data"], b"Shared content")

        files = FileOperations.list_user_files(self.user2.id)
        self.assertGreaterEqual(len(files["shared"]), 1)
        shared_item = next((f for f in files["shared"] if f["id"] == record.id), None)
        self.assertIsNotNone(shared_item)
        self.assertEqual(shared_item["shared_by_username"], "file_user1")
        self.assertIsNotNone(shared_item["shared_at"])

    def test_get_metadata(self):
        record, _ = FileOperations.upload_file(
            "meta.txt", b"Metadata test", self.user1.id
        )
        metadata, _ = FileOperations.get_metadata(record.id, self.user1.id)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["filename"], "meta.txt")
        self.assertEqual(metadata["file_type"], "txt")

    def test_ai_insights(self):
        record, _ = FileOperations.upload_file(
            "insights.txt", b"Project notes. Confidential roadmap details. Budget planning."
            , self.user1.id
        )
        insights, message = FileOperations.get_ai_insights(record.id, self.user1.id)
        self.assertIsNotNone(insights)
        self.assertIn("summary", insights)
        self.assertIn("keywords", insights)
        self.assertIn(insights["sensitivity"], ["low", "medium", "high"])

    def test_read_only_share_cannot_write(self):
        record, _ = FileOperations.upload_file(
            "readonly.txt", b"Owner content", self.user1.id
        )
        success, _ = FileOperations.share_file(
            record.id, "file_user2", "read", self.user1.id
        )
        self.assertTrue(success)

        write_ok, message = FileOperations.write_file(
            record.id, b"Hacked", self.user2.id
        )
        self.assertFalse(write_ok)
        self.assertIn("denied", message.lower())

    def test_file_history_tracks_permission_changes(self):
        record, _ = FileOperations.upload_file(
            "history.txt", b"History", self.user1.id
        )

        success, _ = FileOperations.share_file(
            record.id, "file_user2", "read", self.user1.id
        )
        self.assertTrue(success)

        success, _ = FileOperations.share_file(
            record.id, "file_user2", "write", self.user1.id
        )
        self.assertTrue(success)

        history, _ = FileOperations.get_file_history(record.id, self.user1.id)
        self.assertIsNotNone(history)
        actions = [item["action"] for item in history]
        self.assertIn("FILE_SHARED", actions)
        self.assertIn("FILE_PERMISSION_UPDATED", actions)

    def test_share_history_records_with_timestamp(self):
        record, _ = FileOperations.upload_file(
            "share-records.txt", b"Share records", self.user1.id
        )

        ok, _ = FileOperations.share_file(record.id, "file_user2", "read", self.user1.id)
        self.assertTrue(ok)

        records, _ = FileOperations.get_share_history(self.user1.id)
        self.assertGreaterEqual(len(records), 1)

        matching = next((r for r in records if r["file_id"] == record.id), None)
        self.assertIsNotNone(matching)
        self.assertEqual(matching["target_username"], "file_user2")
        self.assertIn(matching["action"], ["SHARE", "RESHARE", "PERMISSION_UPDATE"])
        self.assertIsNotNone(matching["created_at"])

    def test_list_files(self):
        files = FileOperations.list_user_files(self.user1.id)
        self.assertIn("owned", files)
        self.assertIn("shared", files)
        self.assertGreater(len(files["owned"]), 0)

    def test_share_with_case_insensitive_username(self):
        suffix = uuid.uuid4().hex[:8]
        owner, _ = AuthenticationService.register(f"owner_{suffix}", "Owner123!")
        target, _ = AuthenticationService.register(f"TargetUser_{suffix}", "Target123!")

        record, _ = FileOperations.upload_file(
            "case-share.txt", b"Case share", owner.id
        )

        success, _ = FileOperations.share_file(
            record.id, f"targetuser_{suffix}", "read", owner.id
        )
        self.assertTrue(success)

        result, _ = FileOperations.read_file(record.id, target.id)
        self.assertIsNotNone(result)
        self.assertEqual(result["data"], b"Case share")

    def test_login_with_case_insensitive_username(self):
        suffix = uuid.uuid4().hex[:8]
        mixed_username = f"LoginCase_{suffix}"
        password = "Login123!"
        AuthenticationService.register(mixed_username, password)

        user, message = AuthenticationService.login(mixed_username.lower(), password)
        self.assertIsNotNone(user)
        self.assertIn("successful", message.lower())


if __name__ == '__main__':
    unittest.main()
