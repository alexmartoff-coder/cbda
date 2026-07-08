import aiosqlite
from db.db import DB_PATH

async def get_total_users_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0]

async def get_all_users_data():
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT
                u.user_id,
                u.username,
                u.full_name,
                (SELECT COUNT(*) FROM tickets t WHERE t.user_id = u.user_id) as total_tickets,
                (SELECT COUNT(*) FROM tickets t WHERE t.user_id = u.user_id AND t.type = 'paid') as paid_tickets,
                (SELECT score FROM quiz_sessions qs WHERE qs.user_id = u.user_id) as quiz_score,
                u.created_at,
                (
                    SELECT MAX(last_activity) FROM (
                        SELECT created_at as last_activity FROM tickets WHERE user_id = u.user_id
                        UNION
                        SELECT u.created_at as last_activity
                    )
                ) as last_activity
            FROM users u
        """
        async with db.execute(query) as cursor:
            return await cursor.fetchall()
