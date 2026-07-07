import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT, INITIAL_FAKE_TICKETS

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: 2000 real tickets (visible 2000 if 2000 > 741), TICKET_LIMIT is 2500
        # To trigger by tickets, visible_total must be >= 2500
        mock_count.return_value = 2500
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 1, 1) # Way before deadline

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called()
        # Check channel message
        # The channel message is sent to CHANNEL_ID
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_date(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: 100 real tickets (visible 741), before limit, but after April 10 2026
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 11) # After April 10

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called()
        args, kwargs = bot.send_message.call_args
        self.assertIn("ПРИЁМ БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: 1000 real tickets (visible 1000), before limit (2500), before date
        mock_count.return_value = 1000
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 1, 1)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

if __name__ == '__main__':
    unittest.main()
