import asyncio
import unittest
from keyboards.menu import get_main_menu_keyboard
from config import TICKET_LIMIT

class TestProgress(unittest.IsolatedAsyncioTestCase):
    async def test_progress(self):
        kb, progress = await get_main_menu_keyboard(228592391)
        self.assertIn(str(TICKET_LIMIT), progress)

if __name__ == "__main__":
    unittest.main()
