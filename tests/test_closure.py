import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from database.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('database.db.get_total_tickets_count', new_callable=AsyncMock)
    @patch('database.db.is_collection_closed', new_callable=AsyncMock)
    @patch('database.db.close_collection', new_callable=AsyncMock)
    @patch('database.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed, date before deadline
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 1, 0, 0, 0)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        self.assertGreaterEqual(bot.send_message.call_count, 1)

    @patch('database.db.get_total_tickets_count', new_callable=AsyncMock)
    @patch('database.db.is_collection_closed', new_callable=AsyncMock)
    @patch('database.db.close_collection', new_callable=AsyncMock)
    @patch('database.db.get_moscow_now')
    async def test_closure_by_deadline(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: 0 tickets, not closed, date after deadline (April 10, 2026)
        mock_count.return_value = 0
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 11, 0, 0, 0)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()

    @patch('database.db.get_total_tickets_count', new_callable=AsyncMock)
    @patch('database.db.is_collection_closed', new_callable=AsyncMock)
    @patch('database.db.close_collection', new_callable=AsyncMock)
    @patch('database.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: 1000 tickets, not closed, date before deadline
        mock_count.return_value = 1000
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 1, 0, 0, 0)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

if __name__ == '__main__':
    unittest.main()
