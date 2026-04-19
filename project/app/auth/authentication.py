import re
import bcrypt
from app.models.user import User
from app.models.audit_log import AuditLog


class AuthenticationService:
    # Password policy constants
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128

    @staticmethod
    def validate_username(username):
        """Validate username format: 3-30 alphanumeric/underscore characters."""
        if not username or not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
            return False, "Username must be 3-30 alphanumeric or underscore characters."
        return True, ""

    @staticmethod
    def validate_password(password):
        """Enforce password complexity policy."""
        if not password:
            return False, "Password is required."
        if len(password) < AuthenticationService.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {AuthenticationService.MIN_PASSWORD_LENGTH} characters."
        if len(password) > AuthenticationService.MAX_PASSWORD_LENGTH:
            return False, f"Password must not exceed {AuthenticationService.MAX_PASSWORD_LENGTH} characters."
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter."
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter."
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one digit."
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
            return False, "Password must contain at least one special character."
        return True, ""

    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')

    @staticmethod
    def verify_password(password, password_hash):
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )

    @staticmethod
    def register(username, password, role="user"):
        """Register a new user."""
        username = (username or "").strip()

        valid, msg = AuthenticationService.validate_username(username)
        if not valid:
            return None, msg

        valid, msg = AuthenticationService.validate_password(password)
        if not valid:
            return None, msg

        if User.get_by_username(username):
            return None, "Username already exists."

        password_hash = AuthenticationService.hash_password(password)
        user = User.create(username, password_hash, role)

        AuditLog.log(user.id, "REGISTER", f"user:{user.username}",
                      "User registered successfully")
        return user, "Registration successful."

    @staticmethod
    def login(username, password, ip_address=None):
        """Authenticate a user with username/password."""
        username = (username or "").strip()

        if not username or not password:
            return None, "Username and password are required."

        user = User.get_by_username(username)
        if not user:
            # Use constant-time comparison to avoid timing attacks
            AuthenticationService.hash_password("dummy_password")
            return None, "Invalid username or password."

        if not AuthenticationService.verify_password(password, user.password_hash):
            AuditLog.log(None, "LOGIN_FAILED", f"user:{username}",
                          "Invalid password attempt", ip_address)
            return None, "Invalid username or password."

        if user.two_factor_enabled:
            # Return user but signal that account PIN verification is required.
            AuditLog.log(user.id, "LOGIN_PARTIAL", f"user:{username}",
                          "Password verified, PIN pending", ip_address)
            return user, "PIN_REQUIRED"

        AuditLog.log(user.id, "LOGIN_SUCCESS", f"user:{username}",
                      "User logged in successfully", ip_address)
        return user, "Login successful."
