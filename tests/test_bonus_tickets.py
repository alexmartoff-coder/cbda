import asyncio
import unittest
import os
import aiosqlite
from db.db import init_db, DB_PATH, add_user, mark_rules_accepted, issue_ticket, get_user_applications, set_quiz_session
from handlers.quiz import finish_quiz_logic
from aiogram import Bot
from unittest.mock import AsyncMock, patch

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Always remove test database before running tests
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except OSError:
                pass
        await init_db()

    async def test_bonus_tickets_awarded(self):
        uid = 12345678
        await add_user(uid, "quiz_master", "Quiz Master")
        await mark_rules_accepted(uid)

        # Test with 10 correct answers -> should award +3 bonus tickets (total 4 tickets: 1 base + 3 bonus)
        ticket_num = await issue_ticket(uid, "paid", status="pending")
        self.assertIsNotNone(ticket_num)

        await set_quiz_session(uid, ticket_num, score=10, current_question=10, is_active=True)

        bot_mock = AsyncMock(spec=Bot)
        state_mock = AsyncMock()
        state_mock.get_data.return_value = {}

        # Run finish_quiz_logic
        await finish_quiz_logic(bot_mock, state_mock, uid)

        # Verify bot sent the results message
        bot_mock.send_message.assert_any_call(
            chat_id=uid,
            text=unittest.mock.ANY,
            parse_mode="HTML"
        )

        # Check user's tickets in DB
        tickets = await get_user_applications(uid)
        # Expected: 4 tickets in total
        self.assertEqual(len(tickets), 4)

        # First ticket (base) should be completed with score 10
        base_ticket = [t for t in tickets if t[0] == ticket_num][0]
        self.assertEqual(base_ticket[1], "completed")
        self.assertEqual(base_ticket[2], 10)

        # Bonus tickets should be completed with status 'completed' and not trigger quiz
        bonus_tickets = [t for t in tickets if t[0] != ticket_num]
        self.assertEqual(len(bonus_tickets), 3)
        for t in bonus_tickets:
            self.assertEqual(t[1], "completed")

    async def test_bonus_tickets_9_answers(self):
        uid = 87654321
        await add_user(uid, "silver_player", "Silver Player")
        await mark_rules_accepted(uid)

        # Test with 9 correct answers -> should award +2 bonus tickets (total 3 tickets: 1 base + 2 bonus)
        ticket_num = await issue_ticket(uid, "paid", status="pending")
        await set_quiz_session(uid, ticket_num, score=9, current_question=10, is_active=True)

        bot_mock = AsyncMock(spec=Bot)
        state_mock = AsyncMock()
        state_mock.get_data.return_value = {}

        await finish_quiz_logic(bot_mock, state_mock, uid)

        tickets = await get_user_applications(uid)
        self.assertEqual(len(tickets), 3)

        bonus_tickets = [t for t in tickets if t[0] != ticket_num]
        self.assertEqual(len(bonus_tickets), 2)

    async def test_bonus_tickets_8_answers(self):
        uid = 55555555
        await add_user(uid, "bronze_player", "Bronze Player")
        await mark_rules_accepted(uid)

        # Test with 8 correct answers -> should award +1 bonus ticket (total 2 tickets: 1 base + 1 bonus)
        ticket_num = await issue_ticket(uid, "paid", status="pending")
        await set_quiz_session(uid, ticket_num, score=8, current_question=10, is_active=True)

        bot_mock = AsyncMock(spec=Bot)
        state_mock = AsyncMock()
        state_mock.get_data.return_value = {}

        await finish_quiz_logic(bot_mock, state_mock, uid)

        tickets = await get_user_applications(uid)
        self.assertEqual(len(tickets), 2)

        bonus_tickets = [t for t in tickets if t[0] != ticket_num]
        self.assertEqual(len(bonus_tickets), 1)

    async def test_no_bonus_tickets_under_8(self):
        uid = 44443333
        await add_user(uid, "novice_player", "Novice Player")
        await mark_rules_accepted(uid)

        # Test with 7 correct answers -> should award 0 bonus tickets (total 1 ticket: 1 base)
        ticket_num = await issue_ticket(uid, "paid", status="pending")
        await set_quiz_session(uid, ticket_num, score=7, current_question=10, is_active=True)

        bot_mock = AsyncMock(spec=Bot)
        state_mock = AsyncMock()
        state_mock.get_data.return_value = {}

        await finish_quiz_logic(bot_mock, state_mock, uid)

        tickets = await get_user_applications(uid)
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0][0], ticket_num)

if __name__ == '__main__':
    unittest.main()
