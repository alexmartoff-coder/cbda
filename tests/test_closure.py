import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta
import aiosqlite
from db.db import check_and_trigger_closure, init_db, DB_PATH
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM settings WHERE key = 'is_closure_recorded'")
            await db.execute("UPDATE settings SET value = '0' WHERE key = 'is_closed'")
            await db.commit()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_closure_by_tickets(self, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('db.db.get_moscow_now')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_no_closure(self, mock_close, mock_is_closed, mock_count, mock_now):
        # Setup: date before deadline, 0 tickets, not closed
        mock_now.return_value = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))
        mock_count.return_value = 0
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_already_closed(self, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, already closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = True

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        # close_collection should not be called if already closed
        mock_close.assert_not_called()

if __name__ == '__main__':
    unittest.main()
