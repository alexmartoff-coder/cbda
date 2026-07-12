import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.mark_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_mark, mock_recorded, mock_count):
        # Setup: Reach ticket limit
        mock_count.return_value = TICKET_LIMIT
        mock_recorded.return_value = False
        mock_now.return_value = datetime(2026, 4, 1)

        bot = AsyncMock()
        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        mock_mark.assert_called_once()
        # Should send to channel + start broadcast task
        self.assertGreaterEqual(bot.send_message.call_count, 1)

        args, kwargs = bot.send_message.call_args_list[0]
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.mark_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_date(self, mock_now, mock_close, mock_mark, mock_recorded, mock_count):
        # Setup: Reach deadline
        mock_count.return_value = 100
        mock_recorded.return_value = False
        mock_now.return_value = datetime(2026, 4, 11)

        bot = AsyncMock()
        await check_and_trigger_closure(bot)

        mock_mark.assert_called_once()
        self.assertGreaterEqual(bot.send_message.call_count, 1)

        args, kwargs = bot.send_message.call_args_list[0]
        self.assertIn("Приём билетов окончен", kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.mark_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_already_recorded(self, mock_now, mock_close, mock_mark, mock_recorded, mock_count):
        # Setup: Limit reached but already recorded
        mock_count.return_value = TICKET_LIMIT
        mock_recorded.return_value = True
        mock_now.return_value = datetime(2026, 4, 1)

        bot = AsyncMock()
        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        mock_mark.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
