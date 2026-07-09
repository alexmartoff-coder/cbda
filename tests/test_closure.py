import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT, CONTEST_DEADLINE, INITIAL_FAKE_TICKETS

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: enough tickets to reach limit, not closed, date before deadline
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_now.return_value = datetime.fromisoformat("2026-04-01 12:00:00")

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        # The channel message should be sent
        # We need to find the call where chat_id is CHANNEL_ID
        channel_call = None
        for call in bot.send_message.call_args_list:
            if call.kwargs.get('chat_id') == "@mozgo_boy":
                channel_call = call
                break

        self.assertIsNotNone(channel_call)
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", channel_call.kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_date(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: few tickets, not closed, date AFTER deadline
        mock_count.return_value = 10
        mock_is_closed.return_value = False
        mock_now.return_value = datetime.fromisoformat("2026-04-11 00:00:00")

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        channel_call = None
        for call in bot.send_message.call_args_list:
            if call.kwargs.get('chat_id') == "@mozgo_boy":
                channel_call = call
                break

        self.assertIsNotNone(channel_call)
        self.assertIn("ПРИЁМ БИЛЕТОВ ОКОНЧЕН", channel_call.kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT tickets (total), not closed, before deadline
        mock_count.return_value = TICKET_LIMIT - INITIAL_FAKE_TICKETS - 1
        mock_is_closed.return_value = False
        mock_now.return_value = datetime.fromisoformat("2026-04-01 12:00:00")

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_already_closed(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, already closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = True
        mock_now.return_value = datetime.fromisoformat("2026-04-01 12:00:00")

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

if __name__ == '__main__':
    unittest.main()
