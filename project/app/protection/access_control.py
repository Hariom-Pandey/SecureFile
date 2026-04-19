from app.models.user import User
from app.models.file_record import FileRecord, FilePermission
from app.models.audit_log import AuditLog
from app.models.share_history import ShareHistory


class AccessControlService:
    # Role hierarchy
    ROLES = {
        "admin": 3,
        "user": 2,
        "viewer": 1,
    }

    # Keep RBAC lightweight: role capability checks first, then file ACL checks.
    ACTION_CAPABILITIES = {
        "admin": {"upload", "read", "write", "delete", "share"},
        "user": {"upload", "read", "write", "delete", "share"},
        "viewer": {"read"},
    }

    @staticmethod
    def _get_user(user_id):
        return User.get_by_id(user_id)

    @staticmethod
    def can_perform_action(user_id, action):
        """Check role-based capability for an action before file-level ACL checks."""
        user = AccessControlService._get_user(user_id)
        if not user:
            return False

        role_caps = AccessControlService.ACTION_CAPABILITIES.get(user.role, set())
        return action in role_caps

    @staticmethod
    def can_upload_file(user_id):
        """Check if user role allows uploads."""
        return AccessControlService.can_perform_action(user_id, "upload")

    @staticmethod
    def check_role(user_id, required_role):
        """Check if a user has the required role level."""
        user = AccessControlService._get_user(user_id)
        if not user:
            return False

        user_level = AccessControlService.ROLES.get(user.role, 0)
        required_level = AccessControlService.ROLES.get(required_role, 0)
        return user_level >= required_level

    @staticmethod
    def is_admin(user_id):
        """Check if user is an admin."""
        return AccessControlService.check_role(user_id, "admin")

    @staticmethod
    def can_read_file(user_id, file_id):
        """Check if a user can read a specific file."""
        if not AccessControlService.can_perform_action(user_id, "read"):
            return False

        # Admins can read everything
        if AccessControlService.is_admin(user_id):
            return True

        file_record = FileRecord.get_by_id(file_id)
        if not file_record:
            return False

        # Owner can always read
        if file_record.owner_id == user_id:
            return True

        # Check shared permissions
        permission = FilePermission.get_permission(file_id, user_id)
        return permission in ("read", "write")

    @staticmethod
    def can_write_file(user_id, file_id):
        """Check if a user can write/modify a specific file."""
        if not AccessControlService.can_perform_action(user_id, "write"):
            return False

        if AccessControlService.is_admin(user_id):
            return True

        file_record = FileRecord.get_by_id(file_id)
        if not file_record:
            return False

        if file_record.owner_id == user_id:
            return True

        permission = FilePermission.get_permission(file_id, user_id)
        return permission == "write"

    @staticmethod
    def can_delete_file(user_id, file_id):
        """Check if a user can delete a file (owner or admin only)."""
        if not AccessControlService.can_perform_action(user_id, "delete"):
            return False

        if AccessControlService.is_admin(user_id):
            return True

        file_record = FileRecord.get_by_id(file_id)
        if not file_record:
            return False

        return file_record.owner_id == user_id

    @staticmethod
    def can_share_file(user_id, file_id):
        """Check if a user can share a file (owner or admin only)."""
        if not AccessControlService.can_perform_action(user_id, "share"):
            return False

        if AccessControlService.is_admin(user_id):
            return True

        file_record = FileRecord.get_by_id(file_id)
        if not file_record:
            return False

        return file_record.owner_id == user_id

    @staticmethod
    def share_file(file_id, target_user_id, permission, granted_by):
        """Grant file access to another user."""
        if not AccessControlService.can_share_file(granted_by, file_id):
            return False, "You don't have permission to share this file."

        if permission not in ("read", "write"):
            return False, "Permission must be 'read' or 'write'."

        target_user = User.get_by_id(target_user_id)
        if not target_user:
            return False, "Target user not found."

        file_record = FileRecord.get_by_id(file_id)
        if not file_record:
            return False, "File not found."

        previous_permission = FilePermission.get_permission(file_id, target_user_id)
        FilePermission.grant(file_id, target_user_id, permission, granted_by)

        if previous_permission is None:
            action = "FILE_SHARED"
            details = f"Granted {permission} access to {target_user.username}"
            history_action = "SHARE"
        elif previous_permission != permission:
            action = "FILE_PERMISSION_UPDATED"
            details = (
                f"Permission changed for {target_user.username}: "
                f"{previous_permission} -> {permission}"
            )
            history_action = "PERMISSION_UPDATE"
        else:
            action = "FILE_SHARED"
            details = f"Reconfirmed {permission} access for {target_user.username}"
            history_action = "RESHARE"

        ShareHistory.create_event(
            file_id=file_id,
            sender_user_id=granted_by,
            target_user_id=target_user_id,
            action=history_action,
            permission=permission,
            previous_permission=previous_permission,
        )

        AuditLog.log(
            granted_by,
            action,
            f"file_id:{file_id}",
            details
        )

        return True, f"File shared with {target_user.username} ({permission} access)."

    @staticmethod
    def revoke_access(file_id, target_user_id, revoked_by):
        """Revoke a user's access to a file."""
        if not AccessControlService.can_share_file(revoked_by, file_id):
            return False, "You don't have permission to manage this file's access."

        previous_permission = FilePermission.get_permission(file_id, target_user_id)
        target_user = User.get_by_id(target_user_id)
        FilePermission.revoke(file_id, target_user_id)

        ShareHistory.create_event(
            file_id=file_id,
            sender_user_id=revoked_by,
            target_user_id=target_user_id,
            action="REVOKE",
            permission=None,
            previous_permission=previous_permission,
        )

        target_name = target_user.username if target_user else f"user_id:{target_user_id}"
        AuditLog.log(
            revoked_by,
            "ACCESS_REVOKED",
            f"file_id:{file_id}",
            f"Access revoked for {target_name}"
        )

        return True, "Access revoked successfully."
