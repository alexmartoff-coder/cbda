import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from db.db import issue_ticket, init_db, DB_PATH
import aiosqlite
import os

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()
        # Add a user
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO users (user_id, username, full_name) VALUES (123, 'testuser', 'Test User')")
            await db.commit()

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_bonus_calculation_10(self, mock_closure, mock_kb, mock_finish, mock_update, mock_session):
        from handlers.quiz import finish_quiz_logic
        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        # 10 correct answers
        mock_session.return_value = (10, 10, True, 1) # score, current_q, is_active, t_num
        mock_kb.return_value = (None, "progress")

        await finish_quiz_logic(bot, state, user_id)

        # Check tickets in DB
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND type = 'bonus'", (user_id,)) as c:
                count = (await c.fetchone())[0]

        self.assertEqual(count, 3)

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_bonus_calculation_9(self, mock_closure, mock_kb, mock_finish, mock_update, mock_session):
        from handlers.quiz import finish_quiz_logic
        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        # 9 correct answers
        mock_session.return_value = (9, 10, True, 1)
        mock_kb.return_value = (None, "progress")

        await finish_quiz_logic(bot, state, user_id)

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND type = 'bonus'", (user_id,)) as c:
                count = (await c.fetchone())[0]

        self.assertEqual(count, 2)

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_bonus_calculation_8(self, mock_closure, mock_kb, mock_finish, mock_update, mock_session):
        from handlers.quiz import finish_quiz_logic
        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        # 8 correct answers
        mock_session.return_value = (8, 10, True, 1)
        mock_kb.return_value = (None, "progress")

        await finish_quiz_logic(bot, state, user_id)

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND type = 'bonus'", (user_id,)) as c:
                count = (await c.fetchone())[0]

        self.assertEqual(count, 1)

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_bonus_calculation_low(self, mock_closure, mock_kb, mock_finish, mock_update, mock_session):
        from handlers.quiz import finish_quiz_logic
        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        # 7 correct answers
        mock_session.return_value = (7, 10, True, 1)
        mock_kb.return_value = (None, "progress")

        await finish_quiz_logic(bot, state, user_id)

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND type = 'bonus'", (user_id,)) as c:
                count = (await c.fetchone())[0]

        self.assertEqual(count, 0)

if __name__ == '__main__':
    unittest.main()
