from app.models.database import get_connection


class User:
    def __init__(self, id=None, username=None, password_hash=None, role="user",
                 totp_secret=None, two_factor_enabled=False,
                 created_at=None, updated_at=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.totp_secret = totp_secret
        self.two_factor_enabled = two_factor_enabled
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(username, password_hash, role="user"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return User.get_by_id(user_id)

    @staticmethod
    def get_by_id(user_id):
        conn = get_connection()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if row:
            return User(**dict(row))
        return None

    @staticmethod
    def get_by_username(username):
        if username is None:
            return None

        normalized = username.strip()
        if not normalized:
            return None

        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (normalized,)
        ).fetchone()
        conn.close()
        if row:
            return User(**dict(row))
        return None

    def update_totp_secret(self, secret):
        conn = get_connection()
        conn.execute(
            "UPDATE users SET totp_secret = ?, two_factor_enabled = 1, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (secret, self.id)
        )
        conn.commit()
        conn.close()
        self.totp_secret = secret
        self.two_factor_enabled = True

    def disable_2fa(self):
        conn = get_connection()
        conn.execute(
            "UPDATE users SET totp_secret = NULL, two_factor_enabled = 0, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (self.id,)
        )
        conn.commit()
        conn.close()
        self.totp_secret = None
        self.two_factor_enabled = False

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "two_factor_enabled": bool(self.two_factor_enabled),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
