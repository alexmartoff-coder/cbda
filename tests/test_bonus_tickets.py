import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from db.db import init_db, issue_ticket, get_user_applications, DB_PATH
import aiosqlite

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM tickets")
            await db.execute("DELETE FROM users")
            await db.commit()

    async def test_bonus_tickets_issuance(self):
        user_id = 12345
        from db.db import add_user
        await add_user(user_id, "testuser", "Test User")

        base_t = await issue_ticket(user_id, "base")
        self.assertIsNotNone(base_t)

        b1 = await issue_ticket(user_id, "bonus", status="completed")
        b2 = await issue_ticket(user_id, "bonus", status="completed")
        b3 = await issue_ticket(user_id, "bonus", status="completed")

        self.assertIsNotNone(b1)
        self.assertIsNotNone(b2)
        self.assertIsNotNone(b3)

        apps = await get_user_applications(user_id)
        self.assertEqual(len(apps), 4)

if __name__ == '__main__':
    unittest.main()
