import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.get_moscow_now')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    async def test_closure_by_tickets(self, mock_close, mock_is_closed, mock_now, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed yet, before deadline
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 9, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_any_call(chat_id="@mozgo_boy", text=unittest.mock.ANY)
        # Check text
        args, kwargs = bot.send_message.call_args_list[-1]
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])
        self.assertIn("Мы достигли лимита в 2500 билетов раньше срока", kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.get_moscow_now')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    async def test_closure_by_deadline(self, mock_close, mock_is_closed, mock_now, mock_count):
        # Setup: few tickets, not closed yet, after deadline
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 11, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_any_call(chat_id="@mozgo_boy", text=unittest.mock.ANY)
        # Check text
        args, kwargs = bot.send_message.call_args_list[-1]
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])
        self.assertIn("Приём билетов окончен по наступлению даты 10 апреля 2026", kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.get_moscow_now')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    async def test_no_closure(self, mock_close, mock_is_closed, mock_now, mock_count):
        # Setup: less than TICKET_LIMIT tickets, not closed, before deadline
        from config import INITIAL_FAKE_TICKETS
        mock_count.return_value = TICKET_LIMIT - INITIAL_FAKE_TICKETS - 1
        mock_is_closed.return_value = False
        mock_now.return_value = datetime(2026, 4, 9, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    async def test_already_closed(self, mock_close, mock_is_closed):
        # Setup: already closed recorded
        mock_is_closed.return_value = True

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

if __name__ == '__main__':
    unittest.main()
