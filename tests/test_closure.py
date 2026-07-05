import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT, CONTEST_DEADLINE

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_moscow_now')
    @patch('db.db.get_paid_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_closure_by_tickets(self, mock_close, mock_is_closed, mock_count, mock_now):
        mock_now.return_value = datetime(2026, 1, 1) # Well before deadline
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
    @patch('db.db.get_paid_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_no_closure(self, mock_close, mock_is_closed, mock_count, mock_now):
        mock_now.return_value = datetime(2026, 1, 1) # Well before deadline
        # Setup: less than TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT - 1
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('db.db.get_moscow_now')
    @patch('db.db.get_paid_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_already_closed(self, mock_close, mock_is_closed, mock_count, mock_now):
        mock_now.return_value = datetime(2026, 1, 1)
        # Setup: TICKET_LIMIT tickets, already closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = True

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
