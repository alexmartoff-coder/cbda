import asyncio
import unittest
from unittest.mock import patch
from keyboards.menu import get_main_menu_keyboard

class TestProgress(unittest.IsolatedAsyncioTestCase):
    @patch('keyboards.menu.get_total_tickets_count')
    @patch('keyboards.menu.is_collection_closed')
    async def test_progress_bar_open(self, mock_closed, mock_count):
        mock_closed.return_value = False
        mock_count.return_value = 1250

        kb, progress = await get_main_menu_keyboard(228592391)
        self.assertIn("<b>1250</b>", progress)
        self.assertIn("<b>2500</b>", progress)
        self.assertIn("50%", progress)

    @patch('keyboards.menu.is_collection_closed')
    async def test_progress_bar_closed(self, mock_closed):
        mock_closed.return_value = True

        kb, progress = await get_main_menu_keyboard(228592391)
        self.assertIn("Сбор билетов завершён досрочно!", progress)

if __name__ == "__main__":
    unittest.main()
