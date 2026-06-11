import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from handlers.quiz import finish_quiz_logic

class TestScoring(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_10_correct(self, mock_closure, mock_kb, mock_finish_session, mock_update_res, mock_issue, mock_get_session):
        # Setup: 10 correct answers -> 3 bonus tickets
        user_id = 123
        base_t_num = 1000
        mock_get_session.return_value = (10, 0, True, base_t_num)
        mock_issue.side_effect = [1001, 1002, 1003]
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, user_id)

        # Verify 3 bonus tickets were issued
        self.assertEqual(mock_issue.call_count, 3)

        # Verify message sent to user contains all ticket numbers
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("№01000", kwargs['text'])
        self.assertIn("№01001", kwargs['text'])
        self.assertIn("№01002", kwargs['text'])
        self.assertIn("№01003", kwargs['text'])
        self.assertIn("Начислено билетов: <b>4</b>", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_7_correct(self, mock_closure, mock_kb, mock_finish_session, mock_update_res, mock_issue, mock_get_session):
        # Setup: 7 correct answers -> 0 bonus tickets
        user_id = 123
        base_t_num = 1000
        mock_get_session.return_value = (7, 0, True, base_t_num)
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, user_id)

        # Verify no bonus tickets were issued
        mock_issue.assert_not_called()

        # Verify message sent to user
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("№01000", kwargs['text'])
        self.assertIn("Начислено билетов: <b>1</b>", kwargs['text'])

if __name__ == '__main__':
    unittest.main()
