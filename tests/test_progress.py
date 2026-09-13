import asyncio
import unittest
from unittest.mock import patch
from keyboards.menu import get_main_menu_keyboard
from config import INITIAL_FAKE_TICKETS, TICKET_LIMIT

class TestProgress(unittest.IsolatedAsyncioTestCase):
    @patch('keyboards.menu.is_collection_closed')
    @patch('keyboards.menu.get_total_tickets_count')
    async def test_progress_fake_floor(self, mock_count, mock_closed):
        mock_closed.return_value = False
        mock_count.return_value = 10

        kb, progress = await get_main_menu_keyboard(12345)
        self.assertIn(f"<b>{INITIAL_FAKE_TICKETS}</b>", progress)
        self.assertIn(f"<b>{TICKET_LIMIT}</b>", progress)

    @patch('keyboards.menu.is_collection_closed')
    @patch('keyboards.menu.get_total_tickets_count')
    async def test_progress_real_exceeds_fake(self, mock_count, mock_closed):
        mock_closed.return_value = False
        mock_count.return_value = 1000

        kb, progress = await get_main_menu_keyboard(12345)
        self.assertIn("<b>1000</b>", progress)

if __name__ == '__main__':
    unittest.main()
