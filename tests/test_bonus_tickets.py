import unittest
import asyncio
from db.db import init_db, issue_ticket, get_user_ticket_counts, DB_PATH
import aiosqlite

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM tickets")
            await db.commit()

    async def test_bonus_ticket_issue(self):
        uid = 123456
        base_t = await issue_ticket(uid, "base", status="pending")
        self.assertIsNotNone(base_t)

        bonus1 = await issue_ticket(uid, "bonus", status="completed")
        bonus2 = await issue_ticket(uid, "bonus", status="completed")
        bonus3 = await issue_ticket(uid, "bonus", status="completed")

        self.assertIsNotNone(bonus1)
        self.assertIsNotNone(bonus2)
        self.assertIsNotNone(bonus3)

        total, free = await get_user_ticket_counts(uid)
        self.assertEqual(total, 4)

if __name__ == '__main__':
    unittest.main()
