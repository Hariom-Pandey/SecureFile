from app.models.database import get_connection


class AuditLog:
    @staticmethod
    def log(user_id, action, resource=None, details=None, ip_address=None):
        conn = get_connection()
        conn.execute(
            "INSERT INTO audit_log (user_id, action, resource, details, ip_address) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, action, resource, details, ip_address)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_logs(limit=100, user_id=None):
        conn = get_connection()
        if user_id:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE user_id = ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_file_logs(file_id, limit=100):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM audit_log WHERE resource = ? ORDER BY timestamp DESC LIMIT ?",
            (f"file_id:{file_id}", limit)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
