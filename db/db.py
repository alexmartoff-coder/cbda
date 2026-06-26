import aiosqlite
import os
import asyncio
from datetime import datetime
from aiogram import Bot
from config import TICKET_LIMIT, CHANNEL_ID, MAX_TICKET_NUMBER, CONTEST_DEADLINE
from utils.time_utils import get_moscow_now

DB_PATH = "database/bot_database.db"

async def init_db():
    # Ensure database directory exists
    os.makedirs("database", exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                accepted_rules BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                ticket_number INTEGER UNIQUE,
                type TEXT,
                status TEXT DEFAULT 'pending',
                score INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_seen_questions (
                user_id INTEGER,
                question_id INTEGER,
                PRIMARY KEY (user_id, question_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                user_id INTEGER PRIMARY KEY,
                ticket_number INTEGER,
                score INTEGER DEFAULT 0,
                current_question INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                payload TEXT,
                telegram_payment_charge_id TEXT,
                provider_payment_charge_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS available_tickets (
                ticket_number INTEGER PRIMARY KEY
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event TEXT,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS winners (
                user_id INTEGER,
                ticket_number INTEGER PRIMARY KEY,
                code TEXT,
                won_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)

        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('is_closed', '0')")

        async with db.execute("SELECT COUNT(*) FROM (SELECT ticket_number FROM tickets UNION SELECT ticket_number FROM available_tickets)") as cursor:
            total_count = (await cursor.fetchone())[0]

        if total_count < MAX_TICKET_NUMBER:
            async with db.execute("SELECT MAX(ticket_number) FROM (SELECT ticket_number FROM tickets UNION SELECT ticket_number FROM available_tickets)") as cursor:
                max_num = (await cursor.fetchone())[0] or 0

            batch_size = 5000
            for n_start in range(max_num + 1, MAX_TICKET_NUMBER + 1, batch_size):
                n_end = min(n_start + batch_size, MAX_TICKET_NUMBER + 1)
                batch = [(n,) for n in range(n_start, n_end)]
                await db.executemany("INSERT OR IGNORE INTO available_tickets (ticket_number) VALUES (?)", batch)

        await db.commit()

async def issue_ticket(user_id, ticket_type, status='pending'):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT ticket_number FROM available_tickets ORDER BY ticket_number ASC LIMIT 1") as cursor:
            row = await cursor.fetchone()
            if row:
                ticket_num = row[0]
                await db.execute("DELETE FROM available_tickets WHERE ticket_number = ?", (ticket_num,))
                await db.execute("INSERT INTO tickets (user_id, ticket_number, type, status) VALUES (?, ?, ?, ?)",
                                 (user_id, ticket_num, ticket_type, status))
                await db.commit()
                return ticket_num
    return None

async def update_ticket_result(ticket_number, status, score):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tickets SET status = ?, score = ? WHERE ticket_number = ?", (status, score, ticket_number))
        await db.commit()

async def get_user_applications(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT ticket_number, status, score FROM tickets WHERE user_id = ? ORDER BY created_at", (user_id,)) as cursor:
            return await cursor.fetchall()

async def add_user(user_id, username, full_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
        """, (user_id, username, full_name))
        await db.commit()

async def has_accepted_rules(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT accepted_rules FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] == 1 if row else False

async def mark_rules_accepted(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET accepted_rules = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def set_quiz_session(user_id, ticket_number, score=0, current_question=0, is_active=True):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO quiz_sessions (user_id, ticket_number, score, current_question, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, ticket_number, score, current_question, is_active))
        await db.commit()

async def get_quiz_session(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT score, current_question, is_active, ticket_number FROM quiz_sessions WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def update_quiz_score(user_id, score):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE quiz_sessions SET score = ? WHERE user_id = ?", (score, user_id))
        await db.commit()

async def update_quiz_question(user_id, current_question):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE quiz_sessions SET current_question = ? WHERE user_id = ?", (current_question, user_id))
        await db.commit()

async def finish_quiz_session(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE quiz_sessions SET is_active = 0 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_leaderboard(limit=20):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT
                u.username,
                u.full_name,
                COUNT(t.id) as ticket_count
            FROM users u
            JOIN tickets t ON u.user_id = t.user_id
            GROUP BY u.user_id
            ORDER BY ticket_count DESC
            LIMIT ?
        """, (limit,)) as cursor:
            return await cursor.fetchall()

async def is_collection_closed():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = 'is_closed'") as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0] == '1'
            return False

async def close_collection():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE settings SET value = '1' WHERE key = 'is_closed'")
        now_str = get_moscow_now().replace(tzinfo=None).isoformat()
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('closed_at', ?)", (now_str,))
        await db.commit()

async def get_user_seen_question_ids(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT question_id FROM user_seen_questions WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def mark_questions_as_seen(user_id, question_ids):
    async with aiosqlite.connect(DB_PATH) as db:
        for q_id in question_ids:
            await db.execute("INSERT OR IGNORE INTO user_seen_questions (user_id, question_id) VALUES (?, ?)",
                             (user_id, q_id))
        await db.commit()

async def clear_user_seen_questions(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM user_seen_questions WHERE user_id = ?", (user_id,))
        await db.commit()

async def log_payment(user_id, amount, payload, telegram_id, provider_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO payments (user_id, amount, payload, telegram_payment_charge_id, provider_payment_charge_id)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, amount, payload, telegram_id, provider_id))
        await db.commit()

async def add_system_log(user_id, event, details=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO system_logs (user_id, event, details)
            VALUES (?, ?, ?)
        """, (user_id, event, details))
        await db.commit()

async def get_total_tickets_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM tickets") as cursor:
            row = await cursor.fetchone()
            return row[0]

async def get_paid_tickets_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM tickets WHERE type = 'paid'") as cursor:
            row = await cursor.fetchone()
            return row[0]

async def get_user_ticket_counts(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT type FROM tickets WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            total = len(rows)
            # 'base' can still exist from previous logic or if we mark first ticket as base
            base = sum(1 for (t_type,) in rows if t_type == 'base')
            return total, base

async def check_and_trigger_closure(bot: Bot):
    total_tickets = await get_total_tickets_count()
    is_closed = await is_collection_closed()

    now = get_moscow_now().replace(tzinfo=None)
    deadline = datetime.strptime(CONTEST_DEADLINE, "%Y-%m-%d %H:%M:%S")

    reached_limit = total_tickets >= TICKET_LIMIT
    reached_deadline = now >= deadline

    if (reached_limit or reached_deadline) and not is_closed:
        await close_collection()

        # Bot broadcast text
        if reached_limit:
            broadcast_text = (
                "🎉 Сбор билетов завершён досрочно!\n\n"
                "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
                "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
                "Следи за обновлениями!"
            )
            channel_text = (
                "🔥 СБОР БИЛЕТОВ ЗАВЕРШЁН!\n\n"
                "Мы достигли лимита в 2500 билетов раньше срока.\n"
                "Спасибо всем, кто принял участие!\n\n"
                "Дата и время прямого розыгрыша будет объявлена в ближайшие часы."
            )
        else:
            broadcast_text = (
                "🎉 Приём билетов окончен!\n\n"
                "10 апреля наступило. Спасибо всем участникам!\n\n"
                "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
                "Следи за обновлениями!"
            )
            channel_text = (
                "🔥 ПРИЁМ БИЛЕТОВ ЗАВЕРШЁН!\n\n"
                "10 апреля наступило, приём заявок окончен.\n"
                "Спасибо всем, кто принял участие!\n\n"
                "Дата и время прямого розыгрыша будет объявлена в ближайшие часы."
            )

        async def broadcast_closure_to_all():
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT user_id FROM users") as cursor:
                    all_users = await cursor.fetchall()

            for (uid,) in all_users:
                try:
                    await bot.send_message(uid, broadcast_text)
                    await asyncio.sleep(0.05)
                except:
                    pass

        asyncio.create_task(broadcast_closure_to_all())

        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as e:
            import logging
            logging.error(f"Error sending closure message to channel: {e}")

# Compatibility stubs
async def get_final_times(): return None
async def is_final_active(): return False
