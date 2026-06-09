import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from handlers.quiz import finish_quiz_logic
from aiogram.fsm.context import FSMContext

class TestQuizScoring(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_10(self, mock_closure, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        # Setup: score 10
        mock_session.return_value = (10, 10, True, 100) # score, current_q, is_active, t_num
        mock_issue.side_effect = [200, 201, 202] # bonus ticket numbers
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        # Should issue 3 bonus tickets
        self.assertEqual(mock_issue.call_count, 3)
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("Ты получаешь 3 бонусных билетов", kwargs['text'])
        self.assertIn("№00100, №00200, №00201, №00202", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_9(self, mock_closure, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        # Setup: score 9
        mock_session.return_value = (9, 10, True, 100)
        mock_issue.side_effect = [200, 201]
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        self.assertEqual(mock_issue.call_count, 2)
        self.assertIn("Ты получаешь 2 бонусных билетов", bot.send_message.call_args.kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_8(self, mock_closure, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        # Setup: score 8
        mock_session.return_value = (8, 10, True, 100)
        mock_issue.side_effect = [200]
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        self.assertEqual(mock_issue.call_count, 1)
        self.assertIn("Ты получаешь 1 бонусных билетов", bot.send_message.call_args.kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_7(self, mock_closure, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        # Setup: score 7
        mock_session.return_value = (7, 10, True, 100)
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        self.assertEqual(mock_issue.call_count, 0)
        self.assertIn("Бонусных билетов за этот результат не положено", bot.send_message.call_args.kwargs['text'])

if __name__ == '__main__':
    unittest.main()
