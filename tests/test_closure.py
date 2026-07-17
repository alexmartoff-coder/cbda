import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT

class AsyncContextManagerMock:
    def __init__(self, return_value):
        self.return_value = return_value
    async def __aenter__(self):
        return self.return_value
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    def __await__(self):
        async def _await_helper():
            return self.return_value
        return _await_helper().__await__()

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.get_moscow_now')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('aiosqlite.connect')
    async def test_closure_by_tickets(self, mock_sqlite, mock_close, mock_is_closed, mock_get_now, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT
        mock_get_now.return_value = datetime(2026, 4, 1, 12, 0, 0)
        mock_is_closed.return_value = False

        # Mock sqlite connection and cursor
        mock_db = MagicMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = ('0',) # is_closure_recorded = '0'

        # In aiosqlite, db.execute is a regular method returning a context manager (which is also awaitable)
        mock_db.execute = MagicMock(return_value=AsyncContextManagerMock(mock_cursor))
        mock_db.commit = AsyncMock()
        mock_sqlite.return_value.__aenter__.return_value = mock_db

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.get_moscow_now')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_no_closure(self, mock_close, mock_is_closed, mock_get_now, mock_count):
        # Setup: less than TICKET_LIMIT tickets (including fake ones), not closed, before deadline
        from config import INITIAL_FAKE_TICKETS
        mock_count.return_value = TICKET_LIMIT - INITIAL_FAKE_TICKETS - 1
        mock_get_now.return_value = datetime(2026, 4, 1, 12, 0, 0)
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
