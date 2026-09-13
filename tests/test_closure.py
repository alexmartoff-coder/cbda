import asyncio
import unittest
from unittest.mock import AsyncMock, patch

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_closure_recorded')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_is_closed, mock_count):
        from datetime import datetime
        mock_now.return_value = datetime.fromisoformat("2026-03-01 12:00:00")
        mock_count.return_value = 2500
        mock_is_closed.return_value = False

        from db.db import check_and_trigger_closure
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
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        from datetime import datetime
        mock_now.return_value = datetime.fromisoformat("2026-03-01 12:00:00")
        mock_count.return_value = 100
        mock_is_closed.return_value = False

        from db.db import check_and_trigger_closure
        bot = AsyncMock()
        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
