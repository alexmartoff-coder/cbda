import asyncio
import unittest
from unittest.mock import patch
from keyboards.menu import get_main_menu_keyboard
from db.db import init_db

class TestProgress(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.CONTEST_DEADLINE', '2027-12-31 23:59:59')
    async def test_progress_bar(self):
        await init_db()
        kb, progress = await get_main_menu_keyboard(228592391)
        self.assertIn("2500", progress)
        self.assertIn("Прогресс сбора билетов", progress)

if __name__ == "__main__":
    unittest.main()
