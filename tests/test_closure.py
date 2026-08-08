import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.is_closure_recorded')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.get_moscow_now')
    @patch('db.db.close_collection')
    @patch('db.db.record_closure')
    @patch('keyboards.menu.get_main_menu_keyboard')
    async def test_closure_by_tickets(self, mock_get_kb, mock_record, mock_close_coll, mock_now, mock_total_tickets, mock_is_recorded):
        mock_is_recorded.return_value = False
        mock_total_tickets.return_value = TICKET_LIMIT
        # Mock time to be way before deadline (e.g. April 5, 2026)
        mock_now.return_value = datetime(2026, 4, 5, 12, 0, 0)
        mock_get_kb.return_value = (None, "")

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        # Assertions
        mock_close_coll.assert_called_once()
        mock_record.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertEqual(kwargs['chat_id'], "@mozgo_boy")
        self.assertIn("СБОР БИЛЕТОВ ЗАВЕРШЁН", kwargs['text'])

    @patch('db.db.is_closure_recorded')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.get_moscow_now')
    @patch('db.db.close_collection')
    @patch('db.db.record_closure')
    async def test_no_closure(self, mock_record, mock_close_coll, mock_now, mock_total_tickets, mock_is_recorded):
        mock_is_recorded.return_value = False
        mock_total_tickets.return_value = 100 # way below 2500
        mock_now.return_value = datetime(2026, 4, 5, 12, 0, 0)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close_coll.assert_not_called()
        mock_record.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('db.db.is_closure_recorded')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.get_moscow_now')
    @patch('db.db.close_collection')
    @patch('db.db.record_closure')
    async def test_already_closed(self, mock_record, mock_close_coll, mock_now, mock_total_tickets, mock_is_recorded):
        mock_is_recorded.return_value = True

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close_coll.assert_not_called()
        mock_record.assert_not_called()
        bot.send_message.assert_not_called()

    @patch('db.db.is_closure_recorded')
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.get_moscow_now')
    @patch('db.db.close_collection')
    @patch('db.db.record_closure')
    @patch('keyboards.menu.get_main_menu_keyboard')
    async def test_closure_by_deadline(self, mock_get_kb, mock_record, mock_close_coll, mock_now, mock_total_tickets, mock_is_recorded):
        mock_is_recorded.return_value = False
        mock_total_tickets.return_value = 100 # below 2500 but deadline has passed
        # Mock time to be after deadline (April 11, 2026)
        mock_now.return_value = datetime(2026, 4, 11, 12, 0, 0)
        mock_get_kb.return_value = (None, "")

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close_coll.assert_called_once()
        mock_record.assert_called_once()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertEqual(kwargs['chat_id'], "@mozgo_boy")
        self.assertIn("дедлайна 10 апреля 2026", kwargs['text'])

if __name__ == '__main__':
    unittest.main()
