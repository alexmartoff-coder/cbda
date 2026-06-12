import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from database.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.is_collection_closed_strictly')
    @patch('database.db.close_collection')
    async def test_closure_by_tickets(self, mock_close, mock_is_closed_strictly, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_is_closed_strictly.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called()
        # Verify the target channel message
        target_channel_call = [call for call in bot.send_message.call_args_list if call.kwargs.get('chat_id') == '@mozgo_boy']
        self.assertTrue(len(target_channel_call) > 0)
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", target_channel_call[0].kwargs['text'])

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.is_collection_closed_strictly')
    @patch('database.db.close_collection')
    async def test_no_closure(self, mock_close, mock_is_closed_strictly, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT - 1
        mock_is_closed.return_value = False
        mock_is_closed_strictly.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.is_collection_closed_strictly')
    @patch('database.db.close_collection')
    async def test_already_closed(self, mock_close, mock_is_closed_strictly, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, already closed strictly
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = True
        mock_is_closed_strictly.return_value = True

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
