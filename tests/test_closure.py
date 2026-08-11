import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        import sqlite3
        from db.db import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM settings WHERE key = 'is_closure_recorded'")
        cursor.execute("DELETE FROM settings WHERE key = 'is_closed'")
        conn.commit()
        conn.close()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('utils.time_utils.get_moscow_now')
    async def test_closure_by_tickets(self, mock_get_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed, date is before deadline
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_get_now.return_value = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('utils.time_utils.get_moscow_now')
    async def test_no_closure(self, mock_get_now, mock_close, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT tickets, not closed, date is before deadline
        mock_count.return_value = TICKET_LIMIT - 10
        mock_is_closed.return_value = False
        mock_get_now.return_value = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('utils.time_utils.get_moscow_now')
    async def test_already_closed(self, mock_get_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, already closed, date is before deadline
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = True
        mock_get_now.return_value = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
