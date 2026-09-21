import asyncio
import unittest
from unittest.mock import patch
from keyboards.menu import get_main_menu_keyboard

class TestProgress(unittest.IsolatedAsyncioTestCase):
    @patch('keyboards.menu.is_collection_closed')
    @patch('keyboards.menu.get_total_tickets_count')
    async def test_progress_bar_open(self, mock_count, mock_closed):
        mock_closed.return_value = False
        mock_count.return_value = 100
        kb, progress = await get_main_menu_keyboard(228592391)
        self.assertIn("Собрано билетов", progress)
        self.assertIn("2500", progress)

    @patch('keyboards.menu.is_collection_closed')
    @patch('keyboards.menu.get_total_tickets_count')
    async def test_progress_bar_closed(self, mock_count, mock_closed):
        mock_closed.return_value = True
        mock_count.return_value = 2500
        kb, progress = await get_main_menu_keyboard(228592391)
        self.assertIn("Сбор билетов завершён", progress)
        self.assertIn("2500", progress)

if __name__ == "__main__":
    unittest.main()
