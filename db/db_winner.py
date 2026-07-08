import aiosqlite
from db.db import DB_PATH

async def get_preliminary_winner():
    async with aiosqlite.connect(DB_PATH) as db:
        # Наибольший балл, затем наименьшее время
        query = """
            SELECT ticket_number, user_id, score, total_time
            FROM final_results
            WHERE is_mini_quiz = 0
            ORDER BY score DESC, total_time ASC
            LIMIT 1
        """
        async with db.execute(query) as cursor:
            return await cursor.fetchone()

async def check_for_ties():
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT ticket_number, user_id, score, total_time
            FROM final_results
            WHERE score = (SELECT MAX(score) FROM final_results)
            AND total_time = (SELECT MIN(total_time) FROM final_results WHERE score = (SELECT MAX(score) FROM final_results))
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            return rows if len(rows) > 1 else None

async def setup_mini_quiz(bot, tickets):
    from db.db_final import get_final_times
    times = await get_final_times()
    # Мини-квиз в 21:30

    unique_users = list(set([t[1] for t in tickets]))

    async with aiosqlite.connect(DB_PATH) as db:
        for t_num, u_id, score, time_spent in tickets:
            await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, '1')", (f"mini_quiz_pending_{t_num}",))
        await db.commit()

    for uid in unique_users:
        try:
            await bot.send_message(
                uid,
                f"⚠️ <b>ВНИМАНИЕ!</b>\n\nВ Финале выявлено {len(tickets)} заявок с одинаковыми результатами. "
                "Вы приглашены на финальный мини-квиз!\n\n"
                "Начало в 21:30 МСК.\nДо начала: 00:29:59",
                parse_mode="HTML"
            )
        except: pass

async def get_user_mini_quiz_tickets(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        # Находим билеты пользователя, для которых установлен флаг mini_quiz_pending
        # и которые еще не имеют результата в final_results с is_mini_quiz = 1
        query = """
            SELECT ticket_number FROM tickets
            WHERE user_id = ? AND ticket_number IN (
                SELECT REPLACE(key, 'mini_quiz_pending_', '') FROM settings WHERE key LIKE 'mini_quiz_pending_%' AND value = '1'
            )
            AND ticket_number NOT IN (SELECT ticket_number FROM final_results WHERE is_mini_quiz = 1)
        """
        async with db.execute(query, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

async def get_mini_quiz_winner():
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT ticket_number, user_id, score, total_time
            FROM final_results
            WHERE is_mini_quiz = 1
            ORDER BY score DESC, total_time ASC
            LIMIT 1
        """
        async with db.execute(query) as cursor:
            return await cursor.fetchone()
