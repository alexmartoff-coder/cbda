import asyncio
import unittest
from unittest.mock import AsyncMock, patch
import os
import aiosqlite
from db.db import init_db, DB_PATH, issue_ticket, get_user_ticket_counts
from handlers.quiz import finish_quiz_logic

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        os.makedirs("database", exist_ok=True)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DROP TABLE IF EXISTS users")
            await db.execute("DROP TABLE IF EXISTS tickets")
            await db.execute("DROP TABLE IF EXISTS quiz_sessions")
            await db.execute("DROP TABLE IF EXISTS available_tickets")
            await db.execute("DROP TABLE IF EXISTS settings")
            await db.commit()
        await init_db()

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_quiz_completion_bonus(self, mock_check_closure, mock_get_quiz_session):
        user_id = 999111
        # 1. Issue base ticket for user
        base_num = await issue_ticket(user_id, "paid", status="pending")

        # Mock quiz session returning 10 score
        mock_get_quiz_session.return_value = (10, 10, True, base_num)

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, user_id)

        # Check total tickets for user: 1 paid + 3 bonus = 4
        total, free = await get_user_ticket_counts(user_id)
        self.assertEqual(total, 4)

if __name__ == '__main__':
    unittest.main()
