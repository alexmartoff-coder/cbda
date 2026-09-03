import unittest
from db.db import init_db, add_user, issue_ticket, get_user_applications, DB_PATH
import os
import sqlite3

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Reset DB before test
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()
        await add_user(12345, "testuser", "Test User")

    async def test_bonus_tickets_allocation(self):
        # Issue 1 base ticket
        t_base = await issue_ticket(12345, "base")
        self.assertIsNotNone(t_base)

        # Simulate quiz score 10 -> +3 bonus tickets
        score = 10
        bonus_count = 3 if score == 10 else (2 if score == 9 else (1 if score == 8 else 0))

        for _ in range(bonus_count):
            await issue_ticket(12345, "bonus", status="completed")

        apps = await get_user_applications(12345)
        self.assertEqual(len(apps), 4) # 1 base + 3 bonus

if __name__ == '__main__':
    unittest.main()
