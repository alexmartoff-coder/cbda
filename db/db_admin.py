import aiosqlite
from db.db import DB_PATH

async def get_all_users_data():
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT
                u.user_id,
                u.username,
                u.full_name,
                COUNT(t.id) as total_tickets,
                SUM(CASE WHEN t.type = 'paid' THEN 1 ELSE 0 END) as paid_tickets,
                MAX(t.score) as max_score,
                u.created_at,
                MAX(t.created_at) as last_ticket_at
            FROM users u
            LEFT JOIN tickets t ON u.user_id = t.user_id
            GROUP BY u.user_id
            ORDER BY total_tickets DESC
        """
        async with db.execute(query) as cursor:
            return await cursor.fetchall()
