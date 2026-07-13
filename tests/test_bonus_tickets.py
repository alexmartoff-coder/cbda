import asyncio
import os
import aiosqlite
from db.db import init_db, issue_ticket, get_user_applications, DB_PATH
from handlers.quiz import finish_quiz_logic
from unittest.mock import AsyncMock, MagicMock
from aiogram import Bot
from aiogram.fsm.context import FSMContext

async def test_bonus_tickets():
    # Setup clean DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    await init_db()

    user_id = 12345

    async def run_quiz_test(score, expected_bonus):
        # 1. Issue a base ticket
        t_num = await issue_ticket(user_id, 'paid')

        # 2. Mock state and session
        state = MagicMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={})
        state.clear = AsyncMock()

        bot = MagicMock(spec=Bot)
        bot.send_message = AsyncMock()

        # Manually setup quiz session in DB as finish_quiz_logic expects it
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO quiz_sessions (user_id, ticket_number, score, current_question, is_active) VALUES (?, ?, ?, ?, ?)",
                             (user_id, t_num, score, 10, 1))
            await db.commit()

        # 3. Call finish_quiz_logic
        await finish_quiz_logic(bot, state, user_id)

        # 4. Verify results
        apps = await get_user_applications(user_id)
        # Find tickets issued in this run (base + bonus)
        # Since we clear DB only once at start, we need to be careful.
        # But here we just check total count increment.
        return len(apps)

    print("Testing 10/10 -> +3 bonus (total 4)")
    count = await run_quiz_test(10, 3)
    assert count == 4, f"Expected 4 tickets, got {count}"

    print("Testing 9/10 -> +2 bonus (total 4+3=7)")
    count = await run_quiz_test(9, 2)
    assert count == 7, f"Expected 7 tickets, got {count}"

    print("Testing 8/10 -> +1 bonus (total 7+2=9)")
    count = await run_quiz_test(8, 1)
    assert count == 9, f"Expected 9 tickets, got {count}"

    print("Testing 7/10 -> 0 bonus (total 9+1=10)")
    count = await run_quiz_test(7, 0)
    assert count == 10, f"Expected 10 tickets, got {count}"

    print("✅ Bonus tickets test passed!")

if __name__ == "__main__":
    asyncio.run(test_bonus_tickets())
