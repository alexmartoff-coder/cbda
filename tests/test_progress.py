import asyncio
import unittest
import os
from unittest.mock import patch
from keyboards.menu import get_main_menu_keyboard
from db.db import init_db, DB_PATH

class TestProgress(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()

    @patch('keyboards.menu.is_collection_closed', return_value=False)
    async def test_progress_bar_format(self, mock_is_closed):
        kb, progress = await get_main_menu_keyboard(228592391)
        self.assertIn("<b>741</b>", progress)
        self.assertIn("<b>2500</b>", progress)
        self.assertIn("<b>29%</b>", progress)

if __name__ == "__main__":
    unittest.main()
