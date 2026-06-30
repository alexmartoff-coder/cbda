import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 1)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        # bot.send_message is called multiple times (broadcast + channel)
        self.assertTrue(bot.send_message.called)

        # Check channel message
        from config import CHANNEL_ID
        channel_call = next(c for c in bot.send_message.call_args_list if c.kwargs.get('chat_id') == CHANNEL_ID)
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", channel_call.kwargs['text'])
        self.assertIn("лимита в 2500 билетов", channel_call.kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_date(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT tickets, deadline reached
        mock_count.return_value = 1000
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 11)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        self.assertTrue(bot.send_message.called)

        from config import CHANNEL_ID
        channel_call = next(c for c in bot.send_message.call_args_list if c.kwargs.get('chat_id') == CHANNEL_ID)
        self.assertIn("Приём билетов окончен по расписанию", channel_call.kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT tickets, before deadline
        mock_count.return_value = 1000
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 1)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

if __name__ == '__main__':
    unittest.main()
