import os
import unittest
import aiosqlite
from db.db import init_db, DB_PATH, issue_ticket, get_total_tickets_count
from handlers.quiz import finish_quiz_logic
from unittest.mock import AsyncMock, patch, MagicMock

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Remove old db if exists
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass
        await init_db()

    async def asyncTearDown(self):
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass

    async def test_bonus_tickets_issuance(self):
        user_id = 123456789

        # Issue a paid base ticket
        ticket_num = await issue_ticket(user_id, "paid")
        self.assertIsNotNone(ticket_num)

        # Verify only 1 ticket exists
        count = await get_total_tickets_count()
        self.assertEqual(count, 1)

        # 1. Test 10 correct answers -> should issue +3 bonus tickets
        # Let's mock a quiz session with score=10 and the base ticket_num
        with patch('handlers.quiz.get_quiz_session', new_callable=AsyncMock) as mock_get_session:
            mock_get_session.return_value = (10, 10, True, ticket_num)

            bot = AsyncMock()
            state = AsyncMock()

            await finish_quiz_logic(bot, state, user_id)

            # Check tickets count in DB. It should be 1 base + 3 bonus = 4 total tickets.
            count = await get_total_tickets_count()
            self.assertEqual(count, 4)

            # Check their types and status
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT type, status FROM tickets WHERE user_id = ?", (user_id,)) as cursor:
                    rows = await cursor.fetchall()
                    # Verify types and statuses
                    # Base ticket should be status='completed'
                    base_ticket = [r for r in rows if r[0] == 'paid']
                    self.assertEqual(len(base_ticket), 1)
                    self.assertEqual(base_ticket[0][1], 'completed')

                    # Bonus tickets should be type='bonus' and status='completed'
                    bonus_tickets = [r for r in rows if r[0] == 'bonus']
                    self.assertEqual(len(bonus_tickets), 3)
                    for b_type, b_status in bonus_tickets:
                        self.assertEqual(b_status, 'completed')

if __name__ == "__main__":
    unittest.main()
