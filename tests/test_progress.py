import asyncio
import unittest
from unittest.mock import patch, AsyncMock
from keyboards.menu import get_main_menu_keyboard

class TestProgress(unittest.IsolatedAsyncioTestCase):
    @patch('keyboards.menu.has_accepted_rules')
    @patch('keyboards.menu.get_total_tickets_count')
    @patch('keyboards.menu.is_collection_closed')
    async def test_progress_bar(self, mock_closed, mock_count, mock_rules):
        mock_rules.return_value = True
        mock_count.return_value = 100 # Below the floor of 741
        mock_closed.return_value = False

        kb, progress = await get_main_menu_keyboard(228592391)
        self.assertIn("741", progress) # Should show psychological floor of 741
        self.assertIn("2500", progress)

        mock_count.return_value = 1200 # Above the floor of 741
        kb, progress = await get_main_menu_keyboard(228592391)
        self.assertIn("1200", progress)
        self.assertIn("2500", progress)

if __name__ == "__main__":
    unittest.main()
