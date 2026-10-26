import unittest
from unittest.mock import AsyncMock, patch
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_closure_by_tickets(self, mock_close, mock_is_closed, mock_count):
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    async def test_no_closure(self, mock_close, mock_is_closed, mock_count):
        mock_count.return_value = TICKET_LIMIT - 1
        mock_is_closed.return_value = False

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

if __name__ == '__main__':
    unittest.main()
