import unittest
import os
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch
from aiogram.types import Message, User, Chat
from handlers.payment import show_quiz_play_info
from db.db import init_db, add_user, mark_rules_accepted, close_collection, DB_PATH

class TestMenuAndPayment(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        await init_db()

    @patch.object(Message, 'answer', new_callable=AsyncMock)
    async def test_closed_quiz_info_response(self, mock_answer):
        user = User(id=100, is_bot=False, first_name="Test")
        chat = Chat(id=100, type="private")
        msg = Message(message_id=1, date=datetime.now(), chat=chat, from_user=user, text="🎁 Играть в Квиз за iPhone 17")

        await add_user(100, "test", "Test User")
        await mark_rules_accepted(100)
        await close_collection()

        await show_quiz_play_info(msg)

        mock_answer.assert_called_once()
        args, kwargs = mock_answer.call_args
        self.assertIn("Сбор билетов завершён досрочно!", args[0])

if __name__ == "__main__":
    unittest.main()
