import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config

_test_dir = tempfile.mkdtemp()
Config.DATABASE_PATH = os.path.join(_test_dir, "test_enc.db")
Config.STORAGE_PATH = os.path.join(_test_dir, "storage")
Config.ENCRYPTION_KEY_FILE = os.path.join(_test_dir, "test_enc.key")

from app.protection.encryption import EncryptionService


class TestEncryption(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        EncryptionService.reset()

    def test_encrypt_decrypt_string(self):
        original = "Hello, this is a secret message!"
        encrypted = EncryptionService.encrypt_data(original)
        decrypted = EncryptionService.decrypt_data(encrypted)
        self.assertEqual(decrypted.decode('utf-8'), original)

    def test_encrypt_decrypt_bytes(self):
        original = b'\x00\x01\x02\x03binary data'
        encrypted = EncryptionService.encrypt_data(original)
        decrypted = EncryptionService.decrypt_data(encrypted)
        self.assertEqual(decrypted, original)

    def test_encrypted_differs_from_original(self):
        original = b"sensitive data"
        encrypted = EncryptionService.encrypt_data(original)
        self.assertNotEqual(encrypted, original)

    def test_encrypt_file(self):
        os.makedirs(Config.STORAGE_PATH, exist_ok=True)
        input_path = os.path.join(Config.STORAGE_PATH, "test_input.txt")
        output_path = os.path.join(Config.STORAGE_PATH, "test_output.enc")

        with open(input_path, 'wb') as f:
            f.write(b"File content to encrypt")

        EncryptionService.encrypt_file(input_path, output_path)
        decrypted = EncryptionService.decrypt_file(output_path)
        self.assertEqual(decrypted, b"File content to encrypt")


if __name__ == '__main__':
    unittest.main()
