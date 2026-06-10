import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from database.db import check_and_trigger_closure
from config import TICKET_LIMIT
from datetime import datetime

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed, before deadline
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 3, 25)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        self.assertTrue(bot.send_message.called)

        channel_call = [call for call in bot.send_message.call_args_list if call.kwargs.get('chat_id') == "@mozgo_boy"]
        self.assertTrue(len(channel_call) > 0)
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", channel_call[0].kwargs.get('text'))

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT tickets, not closed, before deadline
        mock_count.return_value = TICKET_LIMIT - 1
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 3, 25)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.get_moscow_now')
    async def test_already_closed(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, already closed, before deadline
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = True
        mock_now.return_value = datetime(2026, 3, 25)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('database.db.get_total_tickets_count')
    @patch('database.db.is_collection_closed')
    @patch('database.db.close_collection')
    @patch('database.db.get_moscow_now')
    async def test_closure_by_date(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: few tickets, not closed, after deadline
        mock_count.return_value = 10
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 11)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        self.assertTrue(bot.send_message.called)

if __name__ == '__main__':
    unittest.main()
