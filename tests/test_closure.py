import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from database.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed, deadline not passed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 1, 12, 0, 0) # Before deadline

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called()

        # Check channel message
        from config import CHANNEL_ID
        channel_call = next(call for call in bot.send_message.call_args_list if call.kwargs.get('chat_id') == CHANNEL_ID)
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", channel_call.kwargs['text'])

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.get_moscow_now')
    async def test_closure_by_deadline(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: 100 tickets (below limit), not closed, deadline passed
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 11, 12, 0, 0) # After deadline

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called()

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT tickets, not closed, before deadline
        mock_count.return_value = TICKET_LIMIT - 1
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 1, 12, 0, 0)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.get_moscow_now')
    async def test_already_closed(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, already closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = True
        mock_now.return_value = datetime(2026, 4, 1, 12, 0, 0)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

if __name__ == '__main__':
    unittest.main()
