from app.models.database import get_connection


class ShareHistory:
    @staticmethod
    def create_event(file_id, sender_user_id, target_user_id, action,
                     permission=None, previous_permission=None):
        conn = get_connection()
        conn.execute(
            "INSERT INTO share_history "
            "(file_id, sender_user_id, target_user_id, action, permission, previous_permission) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (file_id, sender_user_id, target_user_id, action, permission, previous_permission)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_sent_by_user(sender_user_id, limit=200):
        conn = get_connection()
        rows = conn.execute(
            "SELECT sh.id, sh.file_id, sh.sender_user_id, sh.target_user_id, "
            "sh.action, sh.permission, sh.previous_permission, sh.created_at, "
            "f.original_name AS filename, target.username AS target_username "
            "FROM share_history sh "
            "JOIN files f ON f.id = sh.file_id "
            "JOIN users target ON target.id = sh.target_user_id "
            "WHERE sh.sender_user_id = ? "
            "ORDER BY sh.created_at DESC, sh.id DESC "
            "LIMIT ?",
            (sender_user_id, limit)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
