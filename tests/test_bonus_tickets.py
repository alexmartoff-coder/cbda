import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from handlers.quiz import finish_quiz_logic
from aiogram.fsm.context import FSMContext

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('db.db.issue_ticket')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.get_quiz_session')
    async def test_bonus_tickets_10_correct(self, mock_session, mock_update, mock_finish, mock_issue, mock_closure, mock_kb):
        mock_session.return_value = (10, 10, True, 101)
        mock_issue.side_effect = [201, 202, 203]
        mock_kb.return_value = (None, "Progress")

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)

        await finish_quiz_logic(bot, state, 12345)

        self.assertEqual(mock_issue.call_count, 3)
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("Начислено бонусных билетов (3 шт.)", kwargs['text'])

    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('db.db.issue_ticket')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.get_quiz_session')
    async def test_bonus_tickets_7_correct(self, mock_session, mock_update, mock_finish, mock_issue, mock_closure, mock_kb):
        mock_session.return_value = (7, 10, True, 101)
        mock_kb.return_value = (None, "Progress")

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)

        await finish_quiz_logic(bot, state, 12345)

        mock_issue.assert_not_called()
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("Бонусных билетов за эту попытку не получено", kwargs['text'])

if __name__ == '__main__':
    unittest.main()
