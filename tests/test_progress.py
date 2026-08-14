import asyncio
import os
import unittest
from keyboards.menu import get_main_menu_keyboard
from db.db import init_db, DB_PATH, issue_ticket

class TestProgress(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass
        await init_db()

    async def asyncTearDown(self):
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception:
                pass

    async def test_progress_bar_text(self):
        # Fresh DB has 0 real tickets, so progress bar should show INITIAL_FAKE_TICKETS = 741
        kb, progress = await get_main_menu_keyboard(228592391)
        self.assertIn("741", progress)
        self.assertIn("2500", progress)
        self.assertIn("<b>", progress)  # Should use HTML bold tags

if __name__ == "__main__":
    unittest.main()
