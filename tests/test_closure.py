import asyncio
import unittest
import os
from datetime import datetime
from unittest.mock import AsyncMock, patch
from db.db import check_and_trigger_closure, init_db, DB_PATH
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()

    @patch('db.db.get_moscow_now', return_value=datetime(2026, 3, 1, 12, 0, 0))
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.close_collection')
    async def test_closure_by_tickets(self, mock_close, mock_count, mock_time):
        mock_count.return_value = TICKET_LIMIT

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('db.db.get_moscow_now', return_value=datetime(2026, 3, 1, 12, 0, 0))
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.close_collection')
    async def test_no_closure(self, mock_close, mock_count, mock_time):
        mock_count.return_value = TICKET_LIMIT - 100

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
