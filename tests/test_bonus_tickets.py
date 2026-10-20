import unittest
import asyncio
import os
import aiosqlite
from db.db import init_db, issue_ticket, get_user_ticket_counts, DB_PATH
from handlers.quiz import finish_quiz_logic
from unittest.mock import AsyncMock, patch

@patch('db.db.CONTEST_DEADLINE', '2027-12-31 23:59:59')
class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()
        self.user_id = 12345
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO users (user_id, username, full_name, accepted_rules) VALUES (?, ?, ?, 1)",
                             (self.user_id, "test_user", "Test User"))
            await db.commit()

    async def test_bonus_tickets_for_score_10(self):
        t_num = await issue_ticket(self.user_id, "paid", status="pending")
        bot = AsyncMock()

        with patch('handlers.quiz.get_quiz_session', return_value=(10, 10, True, t_num)):
            state = AsyncMock()
            await finish_quiz_logic(bot, state, self.user_id)

        total, free = await get_user_ticket_counts(self.user_id)
        # 1 base + 3 bonus = 4 total tickets
        self.assertEqual(total, 4)

    async def test_bonus_tickets_for_score_9(self):
        t_num = await issue_ticket(self.user_id, "paid", status="pending")
        bot = AsyncMock()

        with patch('handlers.quiz.get_quiz_session', return_value=(9, 10, True, t_num)):
            state = AsyncMock()
            await finish_quiz_logic(bot, state, self.user_id)

        total, free = await get_user_ticket_counts(self.user_id)
        # 1 base + 2 bonus = 3 total tickets
        self.assertEqual(total, 3)

    async def test_bonus_tickets_for_score_8(self):
        t_num = await issue_ticket(self.user_id, "paid", status="pending")
        bot = AsyncMock()

        with patch('handlers.quiz.get_quiz_session', return_value=(8, 10, True, t_num)):
            state = AsyncMock()
            await finish_quiz_logic(bot, state, self.user_id)

        total, free = await get_user_ticket_counts(self.user_id)
        # 1 base + 1 bonus = 2 total tickets
        self.assertEqual(total, 2)

    async def test_no_bonus_tickets_for_score_under_8(self):
        t_num = await issue_ticket(self.user_id, "paid", status="pending")
        bot = AsyncMock()

        with patch('handlers.quiz.get_quiz_session', return_value=(7, 10, True, t_num)):
            state = AsyncMock()
            await finish_quiz_logic(bot, state, self.user_id)

        total, free = await get_user_ticket_counts(self.user_id)
        # 1 base + 0 bonus = 1 total ticket
        self.assertEqual(total, 1)

if __name__ == '__main__':
    unittest.main()
