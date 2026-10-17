import os
import unittest
import aiosqlite
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta
from db.db import DB_PATH, init_db, add_user, mark_rules_accepted, issue_ticket, get_total_tickets_count
from keyboards.menu import get_main_menu_keyboard

class TestMenuAndPayment(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()

    @patch('db.db.get_moscow_now')
    async def test_main_menu_buttons_when_open(self, mock_now):
        mock_now.return_value = datetime(2026, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=3)))
        user_id = 11111
        await add_user(user_id, "user1", "User One")
        await mark_rules_accepted(user_id)

        kb, progress = await get_main_menu_keyboard(user_id)
        button_texts = [btn.text for row in kb.keyboard for btn in row]

        self.assertIn("🎁 Играть в Квиз за iPhone 17", button_texts)
        self.assertIn("📜 Правила розыгрыша", button_texts)
        self.assertIn("🎟️ Мои билеты", button_texts)
        self.assertIn("🏆 Лидерборд", button_texts)
        self.assertIn("❓ Поддержка", button_texts)

    @patch('db.db.get_moscow_now')
    async def test_main_menu_buttons_when_closed(self, mock_now):
        mock_now.return_value = datetime(2026, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=3)))
        user_id = 22222
        await add_user(user_id, "user2", "User Two")

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE settings SET value = '1' WHERE key = 'is_closed'")
            await db.commit()

        kb, progress = await get_main_menu_keyboard(user_id)
        button_texts = [btn.text for row in kb.keyboard for btn in row]

        self.assertNotIn("🎁 Играть в Квиз за iPhone 17", button_texts)
        self.assertIn("📜 Правила розыгрыша", button_texts)
        self.assertIn("🎟️ Мои билеты", button_texts)
        self.assertIn("🏆 Лидерборд", button_texts)
        self.assertIn("❓ Поддержка", button_texts)

if __name__ == '__main__':
    unittest.main()
