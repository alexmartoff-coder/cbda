import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from handlers.quiz import finish_quiz_logic
from db.db import init_db, DB_PATH, issue_ticket
import aiosqlite
import os

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()
        self.user_id = 12345
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO users (user_id, username, full_name, accepted_rules) VALUES (?, ?, ?, 1)",
                             (self.user_id, "testuser", "Test User"))
            await db.commit()

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_3_tickets(self, mock_kb, mock_session):
        # Score 10 -> +3 bonus
        t_num = await issue_ticket(self.user_id, 'base')
        mock_session.return_value = (10, 10, True, t_num) # score, current_q, is_active, t_num
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, self.user_id)

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ?", (self.user_id,)) as cursor:
                count = (await cursor.fetchone())[0]

        # 1 original + 3 bonus = 4
        self.assertEqual(count, 4)

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_2_tickets(self, mock_kb, mock_session):
        # Score 9 -> +2 bonus
        t_num = await issue_ticket(self.user_id, 'base')
        mock_session.return_value = (9, 10, True, t_num)
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, self.user_id)

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ?", (self.user_id,)) as cursor:
                count = (await cursor.fetchone())[0]

        # 1 original + 2 bonus = 3
        self.assertEqual(count, 3)

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_1_ticket(self, mock_kb, mock_session):
        # Score 8 -> +1 bonus
        t_num = await issue_ticket(self.user_id, 'base')
        mock_session.return_value = (8, 10, True, t_num)
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, self.user_id)

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ?", (self.user_id,)) as cursor:
                count = (await cursor.fetchone())[0]

        # 1 original + 1 bonus = 2
        self.assertEqual(count, 2)

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_no_bonus(self, mock_kb, mock_session):
        # Score 7 -> 0 bonus
        t_num = await issue_ticket(self.user_id, 'base')
        mock_session.return_value = (7, 10, True, t_num)
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, self.user_id)

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ?", (self.user_id,)) as cursor:
                count = (await cursor.fetchone())[0]

        # 1 original + 0 bonus = 1
        self.assertEqual(count, 1)

if __name__ == '__main__':
    unittest.main()
