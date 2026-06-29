import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from db.db import check_and_trigger_closure, DB_PATH
from config import TICKET_LIMIT, CONTEST_DEADLINE
import aiosqlite
import os

class TestClosure(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Use a temporary database for testing
        self.db_path = "database/test_bot_database.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        with patch('db.db.DB_PATH', self.db_path):
            from db.db import init_db
            await init_db()

    async def asyncTearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_closure_by_tickets(self, mock_close, mock_is_closed, mock_count):
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False

        bot = AsyncMock()
        with patch('db.db.DB_PATH', self.db_path):
            await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_date(self, mock_now, mock_close, mock_is_closed, mock_count):
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        # Set time to after deadline
        deadline = datetime.fromisoformat(CONTEST_DEADLINE)
        mock_now.return_value = deadline + timedelta(seconds=1)

        bot = AsyncMock()
        with patch('db.db.DB_PATH', self.db_path):
            await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called()

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        mock_count.return_value = TICKET_LIMIT - 1
        mock_is_closed.return_value = False
        deadline = datetime.fromisoformat(CONTEST_DEADLINE)
        mock_now.return_value = deadline - timedelta(seconds=1)

        bot = AsyncMock()
        with patch('db.db.DB_PATH', self.db_path):
            await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

if __name__ == '__main__':
    unittest.main()
