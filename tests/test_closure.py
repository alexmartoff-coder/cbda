import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from database.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed_flag_only')
    @patch('database.db.close_collection')
    async def test_closure_by_tickets(self, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        # bot.send_message is called for each user (in background task) and once for the channel.
        # Since we use asyncio.create_task for broadcast, it might not have finished yet in this test.
        # But the channel message is sent directly after creating the task.
        bot.send_message.assert_called()
        # The last call should be the channel message
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed_flag_only')
    @patch('database.db.close_collection')
    async def test_no_closure(self, mock_close, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT tickets
        mock_count.return_value = TICKET_LIMIT - 1
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed_flag_only')
    @patch('database.db.close_collection')
    async def test_already_closed(self, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, already closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = True

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
