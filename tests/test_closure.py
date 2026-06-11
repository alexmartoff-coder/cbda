import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from database.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 1) # Before deadline

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called() # Should send to channel and users

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.get_moscow_now')
    async def test_closure_by_date(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: below limit, but deadline passed
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 11) # After deadline

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: below limit and before deadline
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 1)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

if __name__ == '__main__':
    unittest.main()
