import unittest
import asyncio
import os
from unittest.mock import AsyncMock
from db.db import init_db, issue_ticket, get_user_applications, DB_PATH
from handlers.quiz import finish_quiz_logic

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()

    async def test_10_correct_answers(self):
        user_id = 12345
        base_ticket = await issue_ticket(user_id, "base")

        from db.db import set_quiz_session
        await set_quiz_session(user_id, base_ticket, score=10, current_question=10, is_active=True)

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, user_id)

        apps = await get_user_applications(user_id)

        # Should have 1 base ticket + 3 bonus tickets = 4 total
        self.assertEqual(len(apps), 4)

        types = [t[3] for t in apps]
        self.assertIn("base", types)
        self.assertEqual(types.count("bonus"), 3)

    async def test_less_than_8_answers(self):
        user_id = 67890
        base_ticket = await issue_ticket(user_id, "base")

        from db.db import set_quiz_session
        await set_quiz_session(user_id, base_ticket, score=7, current_question=10, is_active=True)

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, user_id)

        apps = await get_user_applications(user_id)

        # Should have only 1 base ticket
        self.assertEqual(len(apps), 1)

if __name__ == '__main__':
    unittest.main()
