import aiosqlite
import os
from datetime import datetime
from aiogram import Bot
from config import TICKET_LIMIT, CHANNEL_ID, MAX_TICKET_NUMBER, CONTEST_DEADLINE
from utils.time_utils import get_moscow_now

DB_PATH = "bot_database.db"

async def init_db():
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
        # Сессии прохождения финала (пользователь проходит билеты по очереди)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS final_sessions (
                user_id INTEGER PRIMARY KEY,
                current_ticket_index INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 0,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
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
        # Регистрация в финале (user_id)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS final_registrations (
                user_id INTEGER PRIMARY KEY,
                registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        # Результаты финала для каждого билета
        await db.execute("""
            CREATE TABLE IF NOT EXISTS final_results (
                ticket_number INTEGER PRIMARY KEY,
                user_id INTEGER,
                score INTEGER DEFAULT 0,
                total_time FLOAT DEFAULT 0,
                finished_at DATETIME,
                is_mini_quiz BOOLEAN DEFAULT 0,
                FOREIGN KEY(ticket_number) REFERENCES tickets(ticket_number),
                FOREIGN KEY(user_id) REFERENCES users(user_id)
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

        try:
            await db.execute("ALTER TABLE users ADD COLUMN accepted_rules BOOLEAN DEFAULT 0")
        except:
            pass

        await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('is_closed', '0')")

        async with db.execute("SELECT COUNT(*) FROM (SELECT ticket_number FROM tickets UNION SELECT ticket_number FROM available_tickets)") as cursor:
            total_count = (await cursor.fetchone())[0]

        if total_count < MAX_TICKET_NUMBER:
            async with db.execute("SELECT MAX(ticket_number) FROM (SELECT ticket_number FROM tickets UNION SELECT ticket_number FROM available_tickets)") as cursor:
                max_num = (await cursor.fetchone())[0] or 0

            batch_size = 5000
            for i in range(max_num + 1, MAX_TICKET_NUMBER + 1, batch_size):
                end = min(i + batch_size, MAX_TICKET_NUMBER + 1)
                batch = [(n,) for n in range(i, end)]
                await db.executemany("INSERT OR IGNORE INTO available_tickets (ticket_number) VALUES (?)", batch)

        await db.commit()

async def issue_ticket(user_id, ticket_type):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT ticket_number FROM available_tickets ORDER BY RANDOM() LIMIT 1") as cursor:
            row = await cursor.fetchone()
            if row:
                ticket_num = row[0]
                await db.execute("DELETE FROM available_tickets WHERE ticket_number = ?", (ticket_num,))
                await db.execute("INSERT INTO tickets (user_id, ticket_number, type, status) VALUES (?, ?, ?, 'pending')",
                                 (user_id, ticket_num, ticket_type))
                await db.commit()
                return ticket_num
    return None

async def update_ticket_result(ticket_number, status, score):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tickets SET status = ?, score = ? WHERE ticket_number = ?", (status, score, ticket_number))
        await db.commit()

async def has_user_used_free_attempt(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND type = 'base'", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] > 0

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
            return row[0] == '1'

async def close_collection():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE settings SET value = '1' WHERE key = 'is_closed'")
        # Сохраняем дату закрытия для расчета даты финала (МСК)
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
            free = sum(1 for (t_type,) in rows if t_type == 'base')
            return total, free

async def get_all_finalists():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT DISTINCT user_id FROM tickets WHERE status = 'finalist'") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

async def check_and_trigger_closure(bot: Bot):
    total_count = await get_total_tickets_count()
    now = get_moscow_now().replace(tzinfo=None)

    # Цель - собрать 2500 всего билетов или дождаться дедлайна
    if (total_count >= TICKET_LIMIT or now >= CONTEST_DEADLINE) and not await is_collection_closed():
        await close_collection()

        # Рассылка ВСЕМ пользователям (в фоне)
        from database.db_final import get_final_times
        times = await get_final_times()
        if times:
            async def broadcast_closure_to_all():
                from keyboards.menu import get_main_menu_keyboard
                push_text = (
                    "🎉 Сбор билетов завершён досрочно!\n\n"
                    "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
                    "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
                    "Следи за обновлениями!"
                )

                async with aiosqlite.connect(DB_PATH) as db:
                    async with db.execute("SELECT user_id FROM users") as cursor:
                        all_users = await cursor.fetchall()

                for (uid,) in all_users:
                    try:
                        kb, _ = await get_main_menu_keyboard(uid)
                        await bot.send_message(uid, push_text, parse_mode="HTML", reply_markup=kb)
                        await asyncio.sleep(0.05) # Rate limiting
                    except Exception as e:
                        import logging
                        logging.error(f"Error sending closure message to {uid}: {e}")
            import asyncio
            asyncio.create_task(broadcast_closure_to_all())

        try:
            text = (
                "🔥 СБОР БИЛЕТОВ ЗАВЕРШЁН!\n\n"
                "Мы достигли лимита в 2500 билетов раньше срока.\n"
                "Спасибо всем, кто принял участие!\n\n"
                "Дата и время прямого розыгрыша будет объявлена в ближайшие часы."
            )
            await bot.send_message(chat_id=CHANNEL_ID, text=text)
        except Exception as e:
            import logging
            logging.error(f"Error sending closure message to channel: {e}")
