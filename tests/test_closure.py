import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from db.db import init_db, DB_PATH
        import aiosqlite
        await init_db()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM settings WHERE key = 'is_closure_broadcasted'")
            await db.execute("DELETE FROM settings WHERE key = 'is_closed'")
            await db.commit()

    @patch('db.db.get_moscow_now')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_closure_by_tickets(self, mock_close, mock_is_closed, mock_count, mock_now):
        mock_now.return_value = datetime(2026, 3, 1, 12, 0, 0)
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.side_effect = [False, True]

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('db.db.get_moscow_now')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_no_closure(self, mock_close, mock_is_closed, mock_count, mock_now):
        mock_now.return_value = datetime(2026, 3, 1, 12, 0, 0)
        mock_count.return_value = 0
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('db.db.get_moscow_now')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_already_closed(self, mock_close, mock_is_closed, mock_count, mock_now):
        mock_now.return_value = datetime(2026, 3, 1, 12, 0, 0)
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = True

        from db.db import DB_PATH
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('is_closure_broadcasted', '1')")
            await db.commit()

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()
        bot.send_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
