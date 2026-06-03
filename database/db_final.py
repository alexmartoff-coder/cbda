from datetime import datetime, timedelta
import aiosqlite
from database.db import DB_PATH
from utils.time_utils import get_moscow_now

async def get_final_times():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT key, value FROM settings WHERE key IN ('closed_at', 'test_reg_start')") as cursor:
            rows = await cursor.fetchall()
            settings = {r[0]: r[1] for r in rows}

            if 'test_reg_start' in settings:
                reg_start = datetime.fromisoformat(settings['test_reg_start'])
                reg_end = reg_start + timedelta(minutes=30)
                final_end = reg_start + timedelta(hours=2)
                return {
                    "reg_start": reg_start,
                    "reg_end": reg_end,
                    "final_end": final_end,
                    "is_test": True
                }

            if 'closed_at' not in settings:
                return None

            closed_at = datetime.fromisoformat(settings['closed_at'])
            # Финал на следующий день
            final_date = closed_at.date() + timedelta(days=1)

            reg_start = datetime.combine(final_date, datetime.min.time()).replace(hour=19, minute=0)
            reg_end = reg_start + timedelta(minutes=30)
            final_end = reg_start + timedelta(hours=2) # 21:00

            return {
                "reg_start": reg_start,
                "reg_end": reg_end,
                "final_end": final_end,
                "is_test": False
            }

async def is_final_registration_open():
    times = await get_final_times()
    if not times:
        return False

    now = get_moscow_now().replace(tzinfo=None)
    return times["reg_start"] <= now <= times["reg_end"]

async def is_final_active():
    # Проверяем, не опубликованы ли уже результаты
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = 'results_published'") as cursor:
            if await cursor.fetchone():
                return False

    times = await get_final_times()
    if not times:
        return False

    now = get_moscow_now().replace(tzinfo=None)
    return times["reg_start"] <= now <= times["final_end"]

async def register_for_final(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO final_registrations (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def has_user_registered_for_final(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM final_registrations WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone() is not None

async def get_user_finalist_tickets(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT ticket_number FROM tickets WHERE user_id = ? AND status = 'finalist'", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

async def get_final_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM tickets WHERE status = 'finalist'") as c:
            total_finalists = (await c.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM final_registrations") as c:
            registered_users = (await c.fetchone())[0]
        # Количество зарегистрированных заявок (все финалистские заявки зарегистрированных юзеров)
        async with db.execute("""
            SELECT COUNT(*) FROM tickets
            WHERE status = 'finalist'
            AND user_id IN (SELECT user_id FROM final_registrations)
        """) as c:
            registered_tickets = (await c.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM final_results WHERE is_mini_quiz = 0") as c:
            finished_tickets = (await c.fetchone())[0]

        return {
            "total_finalist_tickets": total_finalists,
            "registered_users": registered_users,
            "registered_tickets": registered_tickets,
            "finished_tickets": finished_tickets
        }
