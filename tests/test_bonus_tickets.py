import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock
from aiogram.fsm.context import FSMContext
from db.db import init_db, issue_ticket, set_quiz_session, get_user_applications, DB_PATH
from handlers.quiz import finish_quiz_logic
import aiosqlite

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM tickets")
            await db.execute("DELETE FROM quiz_sessions")
            await db.commit()

    async def test_bonus_calculation_10(self):
        user_id = 12345
        t_num = await issue_ticket(user_id, "base", status="pending")
        await set_quiz_session(user_id, t_num, score=10, current_question=10, is_active=True)

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)

        await finish_quiz_logic(bot, state, user_id)

        apps = await get_user_applications(user_id)
        # 1 base ticket + 3 bonus tickets = 4 tickets total
        self.assertEqual(len(apps), 4)

    async def test_bonus_calculation_9(self):
        user_id = 12346
        t_num = await issue_ticket(user_id, "base", status="pending")
        await set_quiz_session(user_id, t_num, score=9, current_question=10, is_active=True)

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)

        await finish_quiz_logic(bot, state, user_id)

        apps = await get_user_applications(user_id)
        # 1 base ticket + 2 bonus tickets = 3 tickets total
        self.assertEqual(len(apps), 3)

    async def test_bonus_calculation_8(self):
        user_id = 12347
        t_num = await issue_ticket(user_id, "base", status="pending")
        await set_quiz_session(user_id, t_num, score=8, current_question=10, is_active=True)

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)

        await finish_quiz_logic(bot, state, user_id)

        apps = await get_user_applications(user_id)
        # 1 base ticket + 1 bonus ticket = 2 tickets total
        self.assertEqual(len(apps), 2)

    async def test_bonus_calculation_7(self):
        user_id = 12348
        t_num = await issue_ticket(user_id, "base", status="pending")
        await set_quiz_session(user_id, t_num, score=7, current_question=10, is_active=True)

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)

        await finish_quiz_logic(bot, state, user_id)

        apps = await get_user_applications(user_id)
        # 1 base ticket + 0 bonus tickets = 1 ticket total
        self.assertEqual(len(apps), 1)

if __name__ == '__main__':
    unittest.main()
