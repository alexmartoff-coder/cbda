import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT, CONTEST_DEADLINE

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.mark_closure_recorded')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_mark, mock_close, mock_recorded, mock_count):
        mock_count.return_value = TICKET_LIMIT
        mock_recorded.return_value = False
        mock_now.return_value = datetime.strptime("2026-04-01 12:00:00", "%Y-%m-%d %H:%M:%S")

        bot = AsyncMock()
        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        mock_mark.assert_called_once()
        # bot.send_message should be called for channel and for broadcast task (but task is in background)
        # We at least check the channel message
        bot.send_message.assert_any_call(chat_id="@mozgo_boy", text=unittest.mock.ANY)

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_date(self, mock_now, mock_recorded, mock_count):
        mock_count.return_value = 100
        mock_recorded.return_value = False
        # After deadline
        mock_now.return_value = datetime.strptime("2026-04-11 00:00:00", "%Y-%m-%d %H:%M:%S")

        bot = AsyncMock()
        with patch('db.db.close_collection') as mock_close, patch('db.db.mark_closure_recorded') as mock_mark:
            await check_and_trigger_closure(bot)
            mock_close.assert_called_once()
            mock_mark.assert_called_once()

if __name__ == '__main__':
    unittest.main()
