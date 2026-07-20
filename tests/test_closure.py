import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_get_moscow_now, mock_close, mock_is_closed, mock_count):
        # Return time before deadline
        mock_get_moscow_now.return_value = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))
        # Setup: TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_no_closure(self, mock_get_moscow_now, mock_close, mock_is_closed, mock_count):
        # Return time before deadline
        mock_get_moscow_now.return_value = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))
        # Setup: less than TICKET_LIMIT tickets (including fake ones), not closed
        from config import INITIAL_FAKE_TICKETS
        mock_count.return_value = TICKET_LIMIT - INITIAL_FAKE_TICKETS - 1
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_already_closed(self, mock_get_moscow_now, mock_close, mock_is_closed, mock_count):
        # Return time before deadline
        mock_get_moscow_now.return_value = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))
        # Setup: TICKET_LIMIT tickets, already closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = True

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_deadline(self, mock_get_moscow_now, mock_close, mock_is_closed, mock_count):
        # Return time past deadline
        mock_get_moscow_now.return_value = datetime(2026, 4, 11, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))
        # Setup: less than limit, not closed
        mock_count.return_value = 100
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("Приём билетов окончен", kwargs['text'])

if __name__ == '__main__':
    unittest.main()
