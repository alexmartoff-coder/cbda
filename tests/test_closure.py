import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT, INITIAL_FAKE_TICKETS

class TestClosure(unittest.IsolatedAsyncioTestCase):

    @patch('db.db.get_moscow_now')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.get_paid_tickets_count')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.close_collection')
    async def test_closure_logic(self, mock_close, mock_total_count, mock_paid_count, mock_recorded, mock_now):
        bot = AsyncMock()

        # 1. Test Ticket closure
        mock_now.return_value = datetime(2026, 1, 1)
        mock_recorded.return_value = False
        mock_paid_count.return_value = 0
        mock_total_count.return_value = TICKET_LIMIT # 2500

        await check_and_trigger_closure(bot)
        mock_close.assert_called_once()
        mock_close.reset_mock()

        # 2. Test Date closure
        mock_recorded.return_value = False
        mock_total_count.return_value = 10
        mock_now.return_value = datetime(2026, 5, 1) # After April 10

        await check_and_trigger_closure(bot)
        mock_close.assert_called_once()
        mock_close.reset_mock()

        # 3. Test No closure
        mock_recorded.return_value = False
        mock_total_count.return_value = 10
        mock_now.return_value = datetime(2026, 1, 1)

        await check_and_trigger_closure(bot)
        mock_close.assert_not_called()

    @patch('db.db.get_moscow_now')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.get_paid_tickets_count')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.close_collection')
    async def test_broadcast_trigger(self, mock_close, mock_total_count, mock_paid_count, mock_recorded, mock_now):
        bot = AsyncMock()
        mock_now.return_value = datetime(2026, 1, 1)
        mock_recorded.return_value = False
        mock_total_count.return_value = TICKET_LIMIT

        await check_and_trigger_closure(bot)
        mock_close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
