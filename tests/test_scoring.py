import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from handlers.quiz import finish_quiz_logic

class TestScoring(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_10_correct(self, mock_kb, mock_closure, mock_finish, mock_update, mock_issue, mock_session):
        # Setup: 10/10 score
        mock_session.return_value = [10, 10, True, 12345] # score, current_q, is_active, t_num
        mock_issue.side_effect = [10001, 10002, 10003] # 3 bonus tickets
        mock_kb.return_value = (MagicMock(), "Progress")

        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        # Check if issue_ticket was called 3 times
        self.assertEqual(mock_issue.call_count, 3)

        # Check message
        args, kwargs = bot.send_message.call_args
        self.assertIn("Ты получаешь 3 бонусных билета", kwargs['text'].replace("<b>", "").replace("</b>", ""))

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_7_correct(self, mock_kb, mock_closure, mock_finish, mock_update, mock_issue, mock_session):
        # Setup: 7/10 score
        mock_session.return_value = [7, 10, True, 12345]
        mock_kb.return_value = (MagicMock(), "Progress")

        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        # Check if issue_ticket was called 0 times
        self.assertEqual(mock_issue.call_count, 0)

        # Check message
        args, kwargs = bot.send_message.call_args
        self.assertIn("без бонусов", kwargs['text'])

if __name__ == '__main__':
    unittest.main()
