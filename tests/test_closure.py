import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT, CONTEST_DEADLINE
from utils.time_utils import get_moscow_now

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed, before deadline
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_now.return_value = datetime.fromisoformat(CONTEST_DEADLINE) - timedelta(days=1)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        # Verify channel broadcast (one of the calls to send_message)
        # The bot sends messages to all users (in a task) and one to the channel.
        # Since we're not waiting for the broadcast task, we check the channel one.
        # But wait, the task is created with asyncio.create_task.

        # Give it a tiny bit of time if needed, or just check what's expected
        await asyncio.sleep(0.1)

        found_channel_msg = False
        for call in bot.send_message.call_args_list:
            args, kwargs = call
            if "СБОР БИЛЕТОВ ЗАВЕРШЁН" in kwargs.get('text', ''):
                found_channel_msg = True
                break
        self.assertTrue(found_channel_msg)

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_date(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: few tickets, but deadline reached
        mock_count.return_value = 10
        mock_is_closed.return_value = False
        mock_now.return_value = datetime.fromisoformat(CONTEST_DEADLINE) + timedelta(seconds=1)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT, before deadline
        mock_count.return_value = TICKET_LIMIT - 1
        mock_is_closed.return_value = False
        mock_now.return_value = datetime.fromisoformat(CONTEST_DEADLINE) - timedelta(days=1)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

if __name__ == '__main__':
    unittest.main()
