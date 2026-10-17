import os
import unittest
import aiosqlite
from db.db import DB_PATH, init_db, issue_ticket, add_user, set_quiz_session, finish_quiz_session
from handlers.quiz import finish_quiz_logic
from unittest.mock import AsyncMock

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()

    async def test_bonus_tickets_award(self):
        user_id = 123456
        await add_user(user_id, "testuser", "Test User")

        bot = AsyncMock()

        # Case 1: Score 10 -> +3 bonus tickets
        t_num = await issue_ticket(user_id, "base", status="pending")
        await set_quiz_session(user_id, t_num, score=10, current_question=10, is_active=True)
        state = AsyncMock()
        state.get_data.return_value = {}

        await finish_quiz_logic(bot, state, user_id)

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND type = 'bonus'", (user_id,)) as cursor:
                bonus_count = (await cursor.fetchone())[0]
                self.assertEqual(bonus_count, 3)

if __name__ == '__main__':
    unittest.main()
