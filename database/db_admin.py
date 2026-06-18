import aiosqlite
from database.db import DB_PATH

async def get_all_users_data():
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT
                u.user_id,
                u.username,
                u.full_name,
                (SELECT COUNT(*) FROM tickets t WHERE t.user_id = u.user_id) as total_tickets,
                (SELECT COUNT(*) FROM tickets t WHERE t.user_id = u.user_id AND t.type = 'paid') as paid_tickets,
                (SELECT MAX(score) FROM tickets t WHERE t.user_id = u.user_id) as quiz_score,
                u.created_at,
                (SELECT MAX(created_at) FROM tickets t WHERE t.user_id = u.user_id) as last_activity
            FROM users u
            ORDER BY total_tickets DESC
        """
        async with db.execute(query) as cursor:
            return await cursor.fetchall()
