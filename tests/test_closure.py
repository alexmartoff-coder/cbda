import asyncio
import unittest
import aiosqlite
import os
from datetime import datetime, timedelta
from database.db import check_and_trigger_closure, is_collection_closed, init_db, DB_PATH
from config import CONTEST_DEADLINE, TICKET_LIMIT
from unittest.mock import AsyncMock, patch

class TestClosure(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()

    async def asyncTearDown(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    @patch('database.db.get_moscow_now')
    async def test_is_collection_closed_by_tickets(self, mock_now):
        # Set time before deadline
        deadline_dt = datetime.fromisoformat(CONTEST_DEADLINE)
        mock_now.return_value = (deadline_dt - timedelta(days=1)).replace(tzinfo=None)

        # 1. Initially not closed
        self.assertFalse(await is_collection_closed())

        # 2. Add TICKET_LIMIT tickets
        async with aiosqlite.connect(DB_PATH) as db:
            for i in range(TICKET_LIMIT):
                await db.execute("INSERT INTO tickets (ticket_number, user_id, type) VALUES (?, ?, ?)", (i, 1, 'paid'))
            await db.commit()

        self.assertTrue(await is_collection_closed())

    @patch('database.db.get_moscow_now')
    async def test_is_collection_closed_by_deadline(self, mock_now):
        # Set time after deadline
        deadline_dt = datetime.fromisoformat(CONTEST_DEADLINE)
        mock_now.return_value = (deadline_dt + timedelta(seconds=1)).replace(tzinfo=None)

        self.assertTrue(await is_collection_closed())

    @patch('database.db.get_moscow_now')
    async def test_check_and_trigger_closure(self, mock_now):
        # Set time before deadline
        deadline_dt = datetime.fromisoformat(CONTEST_DEADLINE)
        mock_now.return_value = (deadline_dt - timedelta(days=1)).replace(tzinfo=None)

        # Trigger closure by tickets
        async with aiosqlite.connect(DB_PATH) as db:
            for i in range(TICKET_LIMIT):
                await db.execute("INSERT INTO tickets (ticket_number, user_id, type) VALUES (?, ?, ?)", (i, 1, 'paid'))
            await db.commit()

        bot = AsyncMock()
        await check_and_trigger_closure(bot)

        # Check if bot sent message to channel
        self.assertTrue(bot.send_message.called)

        # Check if is_closed is set in settings
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT value FROM settings WHERE key = 'is_closed'") as cursor:
                row = await cursor.fetchone()
                self.assertEqual(row[0], '1')

if __name__ == '__main__':
    unittest.main()
