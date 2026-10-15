import unittest
import asyncio
import os
import aiosqlite
from db.db import init_db, issue_ticket, get_user_ticket_counts, DB_PATH
from handlers.quiz import finish_quiz_logic
from unittest.mock import AsyncMock, MagicMock

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()

    async def test_bonus_tickets_allocation(self):
        user_id = 12345
        t_num = await issue_ticket(user_id, "base")

        # Mock quiz session in db
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO quiz_sessions (user_id, ticket_number, score, current_question, is_active) VALUES (?, ?, 10, 10, 1)",
                (user_id, t_num)
            )
            await db.commit()

        bot = AsyncMock()
        state = AsyncMock()
        state.get_data.return_value = {}

        await finish_quiz_logic(bot, state, user_id)

        # User should now have 1 base ticket + 3 bonus tickets = 4 tickets total
        total, free = await get_user_ticket_counts(user_id)
        self.assertEqual(total, 4)

if __name__ == "__main__":
    unittest.main()
