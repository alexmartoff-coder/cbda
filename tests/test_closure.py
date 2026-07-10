import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from db.db import check_and_trigger_closure, is_collection_closed
from config import TICKET_LIMIT, CONTEST_DEADLINE

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_now.return_value = datetime.strptime("2025-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called()

        # Check channel message
        channel_call = [call for call in bot.send_message.call_args_list if call.kwargs.get('chat_id') == "@mozgo_boy"]
        self.assertTrue(len(channel_call) > 0)
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", channel_call[0].kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_date(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: 0 tickets, but after deadline
        mock_count.return_value = 0
        mock_is_closed.return_value = False
        # One hour after deadline
        mock_now.return_value = datetime.strptime("2026-04-11 00:59:59", "%Y-%m-%d %H:%M:%S")

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called()
        channel_call = [call for call in bot.send_message.call_args_list if call.kwargs.get('chat_id') == "@mozgo_boy"]
        self.assertTrue(len(channel_call) > 0)
        self.assertIn("Время приёма билетов подошло к концу", channel_call[0].kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT tickets, before deadline
        from config import INITIAL_FAKE_TICKETS
        mock_count.return_value = 0 # visible will be 741
        mock_is_closed.return_value = False
        mock_now.return_value = datetime.strptime("2025-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('db.db.get_moscow_now')
    @patch('aiosqlite.connect')
    async def test_is_collection_closed_by_deadline(self, mock_connect, mock_now):
        # After deadline
        mock_now.return_value = datetime.strptime("2026-04-11 00:00:00", "%Y-%m-%d %H:%M:%S")

        result = await is_collection_closed()
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
