import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT, INITIAL_FAKE_TICKETS

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.mark_closure_recorded')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_mark, mock_close, mock_is_rec, mock_count):
        # Setup: enough tickets to reach limit
        mock_count.return_value = TICKET_LIMIT
        mock_is_rec.return_value = False
        mock_now.return_value = datetime(2026, 1, 1) # Way before deadline

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        mock_mark.assert_called_once()
        # It sends message to channel
        bot.send_message.assert_called()

        # Check channel broadcast
        channel_call = [call for call in bot.send_message.call_args_list if call.kwargs.get('chat_id') == '@mozgo_boy']
        self.assertTrue(len(channel_call) > 0)
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", channel_call[0].kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_rec, mock_count):
        # Setup: less than limit
        mock_count.return_value = 100
        mock_is_rec.return_value = False
        mock_now.return_value = datetime(2026, 1, 1)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.mark_closure_recorded')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_deadline(self, mock_now, mock_mark, mock_close, mock_is_rec, mock_count):
        # Setup: Reached deadline
        mock_count.return_value = 0
        mock_is_rec.return_value = False
        mock_now.return_value = datetime(2026, 4, 11) # After deadline

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        mock_mark.assert_called_once()

        channel_call = [call for call in bot.send_message.call_args_list if call.kwargs.get('chat_id') == '@mozgo_boy']
        self.assertTrue(len(channel_call) > 0)
        self.assertIn("ПРИЁМ БИЛЕТОВ ОКОНЧЕН", channel_call[0].kwargs['text'])

if __name__ == '__main__':
    unittest.main()
