import os
from cryptography.fernet import Fernet
from config import Config


class EncryptionService:
    _fernet = None

    @classmethod
    def _get_fernet(cls):
        """Get or create the Fernet encryption instance."""
        if cls._fernet is None:
            key = cls._load_or_create_key()
            cls._fernet = Fernet(key)
        return cls._fernet

    @staticmethod
    def _load_or_create_key():
        """Load the master encryption key from file, or generate a new one."""
        key_dir = os.path.dirname(Config.ENCRYPTION_KEY_FILE)
        os.makedirs(key_dir, exist_ok=True)
        try:
            os.chmod(key_dir, 0o700)
        except OSError:
            # Permission bits may be ignored on some platforms (e.g., Windows).
            pass

        if os.path.exists(Config.ENCRYPTION_KEY_FILE):
            with open(Config.ENCRYPTION_KEY_FILE, 'rb') as f:
                key = f.read().strip()
            # Validate key shape early to fail fast on corruption.
            Fernet(key)
            return key

        # Refuse to silently generate a new key if encrypted files already exist.
        if EncryptionService._has_existing_encrypted_files():
            raise RuntimeError(
                "Encryption key file is missing while encrypted files exist. "
                "Restore the original key file to access stored files."
            )

        key = Fernet.generate_key()
        # Create key file with restricted permissions
        fd = os.open(Config.ENCRYPTION_KEY_FILE,
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as f:
            f.write(key)
        try:
            os.chmod(Config.ENCRYPTION_KEY_FILE, 0o600)
        except OSError:
            pass
        return key

    @staticmethod
    def _has_existing_encrypted_files():
        storage_dir = Config.STORAGE_PATH
        if not os.path.isdir(storage_dir):
            return False
        for name in os.listdir(storage_dir):
            if name.endswith('.enc'):
                return True
        return False

    @classmethod
    def encrypt_data(cls, data):
        """Encrypt bytes data."""
        fernet = cls._get_fernet()
        if isinstance(data, str):
            data = data.encode('utf-8')
        return fernet.encrypt(data)

    @classmethod
    def decrypt_data(cls, encrypted_data):
        """Decrypt bytes data."""
        fernet = cls._get_fernet()
        return fernet.decrypt(encrypted_data)

    @classmethod
    def encrypt_file(cls, input_path, output_path):
        """Encrypt a file and write to output path."""
        with open(input_path, 'rb') as f:
            data = f.read()

        encrypted = cls.encrypt_data(data)

        with open(output_path, 'wb') as f:
            f.write(encrypted)

        return True

    @classmethod
    def decrypt_file(cls, input_path):
        """Decrypt a file and return the decrypted bytes."""
        with open(input_path, 'rb') as f:
            encrypted_data = f.read()

        return cls.decrypt_data(encrypted_data)

    @classmethod
    def reset(cls):
        """Reset the cached Fernet instance (for testing)."""
        cls._fernet = None
