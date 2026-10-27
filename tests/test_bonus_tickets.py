import unittest
import asyncio
import os
import aiosqlite
from db.db import init_db, issue_ticket, get_user_applications, DB_PATH

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()

    async def test_issue_ticket_with_status(self):
        user_id = 12345
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id, username, full_name, accepted_rules) VALUES (?, ?, ?, 1)",
                             (user_id, "testuser", "Test User"))
            await db.commit()

        base_ticket = await issue_ticket(user_id, "base", status="pending")
        self.assertIsNotNone(base_ticket)

        bonus_ticket1 = await issue_ticket(user_id, "bonus", status="completed")
        bonus_ticket2 = await issue_ticket(user_id, "bonus", status="completed")
        bonus_ticket3 = await issue_ticket(user_id, "bonus", status="completed")

        self.assertIsNotNone(bonus_ticket1)
        self.assertIsNotNone(bonus_ticket2)
        self.assertIsNotNone(bonus_ticket3)

        apps = await get_user_applications(user_id)
        self.assertEqual(len(apps), 4)

        base_apps = [a for a in apps if a[1] == "base"]
        bonus_apps = [a for a in apps if a[1] == "bonus"]

        self.assertEqual(len(base_apps), 1)
        self.assertEqual(len(bonus_apps), 3)

        for b_app in bonus_apps:
            self.assertEqual(b_app[2], "completed")

if __name__ == '__main__':
    unittest.main()
