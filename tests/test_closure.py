import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT, CONTEST_DEADLINE

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_get_moscow_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed, deadline not passed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_get_moscow_now.return_value = datetime.strptime("2026-04-01 12:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=3)))

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
    async def test_closure_by_date(self, mock_get_moscow_now, mock_close, mock_is_closed, mock_count):
        # Setup: less than TICKET_LIMIT tickets, not closed, deadline PASSED
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        mock_get_moscow_now.return_value = datetime.strptime("2026-04-11 12:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=3)))

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
        # Setup: less than TICKET_LIMIT tickets, not closed, deadline not passed
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        mock_get_moscow_now.return_value = datetime.strptime("2026-04-01 12:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=3)))

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_already_closed(self, mock_get_moscow_now, mock_close, mock_is_closed, mock_count):
        # Setup: already closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = True
        mock_get_moscow_now.return_value = datetime.strptime("2026-04-01 12:00:00", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone(timedelta(hours=3)))

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
