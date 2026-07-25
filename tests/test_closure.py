import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from db.db import check_and_trigger_closure

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_moscow_now')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.close_collection')
    async def test_closure_by_tickets(self, mock_close, mock_count, mock_is_recorded, mock_get_now):
        # Setup: 2500 tickets, not recorded, before deadline
        mock_is_recorded.return_value = False
        mock_count.return_value = 2500
        mock_get_now.return_value = datetime(2026, 3, 1, 12, 0, 0)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('db.db.get_moscow_now')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.close_collection')
    async def test_no_closure(self, mock_close, mock_count, mock_is_recorded, mock_get_now):
        # Setup: less than TICKET_LIMIT tickets, not recorded, before deadline
        mock_is_recorded.return_value = False
        mock_count.return_value = 500
        mock_get_now.return_value = datetime(2026, 3, 1, 12, 0, 0)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('db.db.get_moscow_now')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.close_collection')
    async def test_already_closed(self, mock_close, mock_count, mock_is_recorded, mock_get_now):
        # Setup: TICKET_LIMIT tickets, already recorded, before deadline
        mock_is_recorded.return_value = True
        mock_count.return_value = 2500
        mock_get_now.return_value = datetime(2026, 3, 1, 12, 0, 0)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
