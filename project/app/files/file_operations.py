import os
import uuid
from config import Config
from app.models.file_record import FileRecord, FilePermission
from app.models.audit_log import AuditLog
from app.models.share_history import ShareHistory
from app.files.intelligence import FileIntelligenceService
from app.protection.encryption import EncryptionService
from app.protection.access_control import AccessControlService
from app.detection.threat_detector import ThreatDetector


class FileOperations:

    @staticmethod
    def _ensure_storage():
        """Ensure the storage directory exists."""
        os.makedirs(Config.STORAGE_PATH, exist_ok=True)
        try:
            os.chmod(Config.STORAGE_PATH, 0o700)
        except OSError:
            # Permission bits may be ignored on some platforms (e.g., Windows).
            pass

    @staticmethod
    def _write_bytes_secure(file_path, content):
        """Write bytes atomically to avoid partial-file corruption."""
        tmp_path = file_path + ".tmp"
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, file_path)
            try:
                os.chmod(file_path, 0o600)
            except OSError:
                pass
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    @staticmethod
    def upload_file(filename, file_data, user_id):
        """Upload and encrypt a file."""
        if not AccessControlService.can_upload_file(user_id):
            AuditLog.log(
                user_id,
                "ACCESS_DENIED",
                "file_upload",
                "Upload denied by RBAC role policy"
            )
            return None, ["Access denied. Your role is not allowed to upload files."]

        # Security scan
        safe, messages = ThreatDetector.scan_file_upload(
            filename, file_data, user_id
        )
        if not safe:
            return None, messages

        FileOperations._ensure_storage()

        # Generate unique internal filename
        ext = os.path.splitext(filename)[1].lower()
        internal_name = f"{uuid.uuid4().hex}.enc"
        file_path = os.path.join(Config.STORAGE_PATH, internal_name)

        # Encrypt and save
        encrypted_data = EncryptionService.encrypt_data(file_data)
        FileOperations._write_bytes_secure(file_path, encrypted_data)

        # Determine file type
        file_type = ext.lstrip('.') if ext else "unknown"

        # Create database record
        record = FileRecord.create(
            filename=internal_name,
            original_name=filename,
            owner_id=user_id,
            file_size=len(file_data),
            file_type=file_type,
        )

        AuditLog.log(
            user_id,
            "FILE_UPLOAD",
            f"file_id:{record.id}",
            f"File uploaded: {filename} ({len(file_data)} bytes)"
        )

        return record, ["File uploaded and encrypted successfully."]

    @staticmethod
    def read_file(file_id, user_id):
        """Read and decrypt a file (with access control check)."""
        if not AccessControlService.can_read_file(user_id, file_id):
            AuditLog.log(user_id, "ACCESS_DENIED", f"file_id:{file_id}",
                          "Read access denied")
            return None, "Access denied. You don't have read permission."

        record = FileRecord.get_by_id(file_id)
        if not record:
            return None, "File not found."

        file_path = os.path.join(Config.STORAGE_PATH, record.filename)
        if not os.path.exists(file_path):
            return None, "File data not found on disk."

        # Decrypt file and fail gracefully on corruption/key mismatch.
        try:
            decrypted_data = EncryptionService.decrypt_file(file_path)
        except Exception:
            AuditLog.log(
                user_id,
                "FILE_DECRYPT_FAILED",
                f"file_id:{record.id}",
                "Decryption failed for stored file data"
            )
            return None, "File data is unreadable or encryption key is invalid."

        AuditLog.log(
            user_id,
            "FILE_READ",
            f"file_id:{record.id}",
            f"File read: {record.original_name}"
        )

        return {
            "filename": record.original_name,
            "data": decrypted_data,
            "file_type": record.file_type,
            "size": record.file_size,
        }, "File retrieved successfully."

    @staticmethod
    def write_file(file_id, new_data, user_id):
        """Overwrite a file's content (with access control and threat scan)."""
        if not AccessControlService.can_write_file(user_id, file_id):
            AuditLog.log(user_id, "ACCESS_DENIED", f"file_id:{file_id}",
                          "Write access denied")
            return False, "Access denied. You don't have write permission."

        record = FileRecord.get_by_id(file_id)
        if not record:
            return False, "File not found."

        # Scan new content
        safe, messages = ThreatDetector.scan_file_upload(
            record.original_name, new_data, user_id
        )
        if not safe:
            return False, messages

        # Encrypt and overwrite
        file_path = os.path.join(Config.STORAGE_PATH, record.filename)
        encrypted_data = EncryptionService.encrypt_data(new_data)
        FileOperations._write_bytes_secure(file_path, encrypted_data)

        # Update record
        from app.models.database import get_connection
        conn = get_connection()
        conn.execute(
            "UPDATE files SET file_size = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (len(new_data), file_id)
        )
        conn.commit()
        conn.close()

        AuditLog.log(
            user_id,
            "FILE_WRITE",
            f"file_id:{record.id}",
            f"File updated: {record.original_name} ({len(new_data)} bytes)"
        )

        return True, "File updated successfully."

    @staticmethod
    def delete_file(file_id, user_id):
        """Delete a file (with access control check)."""
        if not AccessControlService.can_delete_file(user_id, file_id):
            AuditLog.log(user_id, "ACCESS_DENIED", f"file_id:{file_id}",
                          "Delete access denied")
            return False, "Access denied. Only the owner or admin can delete files."

        record = FileRecord.get_by_id(file_id)
        if not record:
            return False, "File not found."

        # Delete the physical file
        file_path = os.path.join(Config.STORAGE_PATH, record.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                AuditLog.log(
                    user_id,
                    "FILE_DELETE_FAILED",
                    f"file_id:{record.id}",
                    "Failed to delete encrypted file from disk"
                )
                return False, "Failed to delete file data from disk."

        # Delete the database record (cascades to permissions)
        record.delete()

        AuditLog.log(
            user_id,
            "FILE_DELETE",
            f"file_id:{record.id}",
            f"File deleted: {record.original_name}"
        )

        return True, "File deleted successfully."

    @staticmethod
    def get_metadata(file_id, user_id):
        """Get file metadata (with access control check)."""
        if not AccessControlService.can_read_file(user_id, file_id):
            return None, "Access denied."

        record = FileRecord.get_by_id(file_id)
        if not record:
            return None, "File not found."

        # Get permissions list if user is owner or admin
        permissions = []
        if record.owner_id == user_id or AccessControlService.is_admin(user_id):
            permissions = FilePermission.get_file_permissions(file_id)

        metadata = record.to_dict()
        metadata["permissions"] = permissions

        AuditLog.log(
            user_id,
            "FILE_METADATA",
            f"file_id:{record.id}",
            f"Metadata viewed: {record.original_name}"
        )

        return metadata, "Metadata retrieved."

    @staticmethod
    def get_file_history(file_id, user_id, limit=100):
        """Get audit history for a file (access-controlled)."""
        if not AccessControlService.can_read_file(user_id, file_id):
            return None, "Access denied."

        record = FileRecord.get_by_id(file_id)
        if not record:
            return None, "File not found."

        history = AuditLog.get_file_logs(file_id, limit=limit)
        return history, "History retrieved."

    @staticmethod
    def get_share_history(user_id, limit=200):
        """Get records of files shared by the given user."""
        records = ShareHistory.get_sent_by_user(user_id, limit=limit)
        return records, "Share records retrieved."

    @staticmethod
    def get_ai_insights(file_id, user_id):
        """Generate local AI-style insights for a file."""
        if not AccessControlService.can_read_file(user_id, file_id):
            AuditLog.log(user_id, "ACCESS_DENIED", f"file_id:{file_id}", "Insights access denied")
            return None, "Access denied. You don't have read permission."

        record = FileRecord.get_by_id(file_id)
        if not record:
            return None, "File not found."

        file_path = os.path.join(Config.STORAGE_PATH, record.filename)
        if not os.path.exists(file_path):
            return None, "File data not found on disk."

        try:
            decrypted_data = EncryptionService.decrypt_file(file_path)
        except Exception:
            AuditLog.log(
                user_id,
                "FILE_DECRYPT_FAILED",
                f"file_id:{record.id}",
                "Decryption failed while generating insights"
            )
            return None, "File data is unreadable or encryption key is invalid."

        insights = FileIntelligenceService.build_insights(record, decrypted_data)

        AuditLog.log(
            user_id,
            "FILE_INSIGHTS",
            f"file_id:{record.id}",
            f"AI-style insights generated for {record.original_name}"
        )

        return insights, "Insights generated successfully."

    @staticmethod
    def list_user_files(user_id):
        """List all files owned by or shared with a user."""
        owned = FileRecord.get_by_owner(user_id)
        shared = FileRecord.get_shared_with_user(user_id)

        return {
            "owned": [f.to_dict() for f in owned],
            "shared": [f.to_dict() for f in shared],
        }

    @staticmethod
    def share_file(file_id, target_username, permission, user_id):
        """Share a file with another user by username."""
        from app.models.user import User
        normalized_username = (target_username or "").strip()
        target = User.get_by_username(normalized_username)
        if not target:
            return False, "Target user not found."

        if target.id == user_id:
            return False, "Cannot share a file with yourself."

        return AccessControlService.share_file(
            file_id, target.id, permission, user_id
        )
