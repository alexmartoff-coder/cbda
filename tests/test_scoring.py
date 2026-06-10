import asyncio
from handlers.quiz import finish_quiz_logic
from database.db import init_db, add_user, set_quiz_session, get_user_applications
from unittest.mock import AsyncMock, MagicMock
import os

async def test_scoring():
    db_path = "bot_database.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    await init_db()

    user_id = 12345
    await add_user(user_id, "testuser", "Test User")

    bot = AsyncMock()
    state = AsyncMock()

    async def run_test(score, expected_bonus):
        # Create a base ticket
        from database.db import issue_ticket
        t_num = await issue_ticket(user_id, "base")
        await set_quiz_session(user_id, t_num, score=score, current_question=10, is_active=True)

        await finish_quiz_logic(bot, state, user_id)

        apps = await get_user_applications(user_id)
        # Filter for bonus tickets created in this run
        # Note: this is a bit simplistic since tickets are added to the same DB
        bonus_tickets = [t for t in apps if t[1] == 'pending' or t[1] == 'completed'] # types are not in get_user_applications results
        # Actually get_user_applications returns (ticket_number, status, score)

        from database.db import DB_PATH
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT type FROM tickets WHERE user_id = ? AND type = 'bonus'", (user_id,)) as cursor:
                bonuses = await cursor.fetchall()
                return len(bonuses)

    print("Testing 10/10...")
    count = await run_test(10, 3)
    print(f"Bonus count: {count}")
    if count != 3: print(f"FAILED: Expected 3, got {count}")

    print("Testing 9/10...")
    # Clear bonus tickets for next test
    import aiosqlite
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("DELETE FROM tickets WHERE type = 'bonus'")
        await db.commit()
    count = await run_test(9, 2)
    print(f"Bonus count: {count}")
    if count != 2: print(f"FAILED: Expected 2, got {count}")

    print("Testing 8/10...")
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("DELETE FROM tickets WHERE type = 'bonus'")
        await db.commit()
    count = await run_test(8, 1)
    print(f"Bonus count: {count}")
    if count != 1: print(f"FAILED: Expected 1, got {count}")

    print("Testing 7/10...")
    async with aiosqlite.connect("bot_database.db") as db:
        await db.execute("DELETE FROM tickets WHERE type = 'bonus'")
        await db.commit()
    count = await run_test(7, 0)
    print(f"Bonus count: {count}")
    if count != 0: print(f"FAILED: Expected 0, got {count}")

    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    asyncio.run(test_scoring())
