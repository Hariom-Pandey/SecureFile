from app.models.database import get_connection


class FileRecord:
    def __init__(self, id=None, filename=None, original_name=None,
                 owner_id=None, file_size=0, file_type=None,
                 is_encrypted=True, created_at=None, updated_at=None,
                 owner_username=None, shared_permission=None,
                 shared_by_username=None, shared_at=None,
                 permission_updated_at=None):
        self.id = id
        self.filename = filename
        self.original_name = original_name
        self.owner_id = owner_id
        self.file_size = file_size
        self.file_type = file_type
        self.is_encrypted = is_encrypted
        self.created_at = created_at
        self.updated_at = updated_at
        self.owner_username = owner_username
        self.shared_permission = shared_permission
        self.shared_by_username = shared_by_username
        self.shared_at = shared_at
        self.permission_updated_at = permission_updated_at

    @staticmethod
    def create(filename, original_name, owner_id, file_size, file_type):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (filename, original_name, owner_id, file_size, file_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (filename, original_name, owner_id, file_size, file_type)
        )
        conn.commit()
        file_id = cursor.lastrowid
        conn.close()
        return FileRecord.get_by_id(file_id)

    @staticmethod
    def get_by_id(file_id):
        conn = get_connection()
        row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
        conn.close()
        if row:
            return FileRecord(**dict(row))
        return None

    @staticmethod
    def get_by_owner(owner_id):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM files WHERE owner_id = ? ORDER BY created_at DESC",
            (owner_id,)
        ).fetchall()
        conn.close()
        return [FileRecord(**dict(row)) for row in rows]

    @staticmethod
    def get_shared_with_user(user_id):
        conn = get_connection()
        rows = conn.execute(
            "SELECT f.*, owner.username AS owner_username, "
            "fp.permission AS shared_permission, "
            "fp.created_at AS shared_at, "
            "fp.updated_at AS permission_updated_at, "
            "granter.username AS shared_by_username "
            "FROM files f "
            "JOIN file_permissions fp ON f.id = fp.file_id "
            "JOIN users owner ON owner.id = f.owner_id "
            "LEFT JOIN users granter ON granter.id = fp.granted_by "
            "WHERE fp.user_id = ? "
            "ORDER BY fp.created_at DESC, f.created_at DESC",
            (user_id,)
        ).fetchall()
        conn.close()
        return [FileRecord(**dict(row)) for row in rows]

    def delete(self):
        conn = get_connection()
        conn.execute("DELETE FROM files WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.original_name,
            "owner_id": self.owner_id,
            "owner_username": self.owner_username,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "is_encrypted": bool(self.is_encrypted),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "shared_permission": self.shared_permission,
            "shared_by_username": self.shared_by_username,
            "shared_at": self.shared_at,
            "permission_updated_at": self.permission_updated_at,
        }


class FilePermission:
    @staticmethod
    def grant(file_id, user_id, permission, granted_by):
        conn = get_connection()
        conn.execute(
            "INSERT INTO file_permissions (file_id, user_id, permission, granted_by) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(file_id, user_id) DO UPDATE SET "
            "permission = excluded.permission, "
            "granted_by = excluded.granted_by, "
            "updated_at = CURRENT_TIMESTAMP",
            (file_id, user_id, permission, granted_by)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def revoke(file_id, user_id):
        conn = get_connection()
        conn.execute(
            "DELETE FROM file_permissions WHERE file_id = ? AND user_id = ?",
            (file_id, user_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_permission(file_id, user_id):
        conn = get_connection()
        row = conn.execute(
            "SELECT permission FROM file_permissions "
            "WHERE file_id = ? AND user_id = ?",
            (file_id, user_id)
        ).fetchone()
        conn.close()
        if row:
            return row["permission"]
        return None

    @staticmethod
    def get_file_permissions(file_id):
        conn = get_connection()
        rows = conn.execute(
            "SELECT fp.id, fp.file_id, fp.user_id, fp.permission, fp.granted_by, "
            "fp.created_at, fp.updated_at, "
            "u.username AS username, gu.username AS granted_by_username "
            "FROM file_permissions fp "
            "JOIN users u ON fp.user_id = u.id "
            "LEFT JOIN users gu ON fp.granted_by = gu.id "
            "WHERE fp.file_id = ? "
            "ORDER BY fp.updated_at DESC, fp.created_at DESC",
            (file_id,)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
