import re
import bcrypt
from app.models.user import User
from app.models.audit_log import AuditLog


class TwoFactorAuth:
    PIN_PATTERN = re.compile(r'^\d{6}$')

    @staticmethod
    def _validate_pin(pin_code):
        if not isinstance(pin_code, str):
            return False, "PIN is required."

        if not TwoFactorAuth.PIN_PATTERN.match(pin_code):
            return False, "PIN must be exactly 6 digits."

        return True, ""

    @staticmethod
    def _hash_pin(pin_code):
        return bcrypt.hashpw(pin_code.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

    @staticmethod
    def setup_2fa(user_id, pin_code):
        """Enable account PIN lock (simple second-step login)."""
        user = User.get_by_id(user_id)
        if not user:
            return None, "User not found."

        valid, message = TwoFactorAuth._validate_pin(pin_code)
        if not valid:
            return None, message

        pin_hash = TwoFactorAuth._hash_pin(pin_code)
        user.update_totp_secret(pin_hash)
        AuditLog.log(user_id, "PIN_LOCK_ENABLED", f"user:{user.username}",
                     "Account PIN lock enabled")
        return {"enabled": True}, "PIN lock enabled successfully."

    @staticmethod
    def confirm_2fa(user_id, _secret, pin_code):
        """Backward-compatible alias that enables PIN lock."""
        return TwoFactorAuth.setup_2fa(user_id, pin_code)

    @staticmethod
    def verify_otp(user_id, otp_code):
        """Verify account PIN during login second step."""
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found."
        if not user.totp_secret:
            return False, "PIN lock is not enabled for this user."

        valid, message = TwoFactorAuth._validate_pin(otp_code)
        if not valid:
            AuditLog.log(user_id, "PIN_VERIFY_FAILED", f"user:{user.username}", message)
            return False, message

        is_valid = bcrypt.checkpw(
            otp_code.encode('utf-8'),
            user.totp_secret.encode('utf-8')
        )

        if is_valid:
            AuditLog.log(user_id, "PIN_VERIFIED", f"user:{user.username}",
                         "PIN verified successfully")
            return True, "PIN verified."

        AuditLog.log(user_id, "PIN_VERIFY_FAILED", f"user:{user.username}",
                     "Invalid PIN attempt")
        return False, "Invalid PIN."

    @staticmethod
    def disable_2fa(user_id):
        """Disable account PIN lock for a user."""
        user = User.get_by_id(user_id)
        if not user:
            return False, "User not found."

        user.disable_2fa()
        AuditLog.log(user_id, "PIN_LOCK_DISABLED", f"user:{user.username}",
                     "Account PIN lock disabled")
        return True, "PIN lock disabled."
