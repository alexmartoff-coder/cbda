import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT, INITIAL_FAKE_TICKETS

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2025, 1, 1)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        # bot.send_message is called for channel and for broadcast
        self.assertTrue(bot.send_message.called)

        # Check channel message
        # The channel message is the one with the CHANNEL_ID (from config)
        channel_call = None
        for call in bot.send_message.call_args_list:
            if call.kwargs.get('chat_id') == "@mozgo_boy":
                channel_call = call
                break

        self.assertIsNotNone(channel_call)
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", channel_call.kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT - INITIAL_FAKE_TICKETS - 1
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2025, 1, 1)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_deadline(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: past deadline
        mock_count.return_value = 0
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 11)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
