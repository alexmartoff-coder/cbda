import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from handlers.quiz import finish_quiz_logic

class TestScoring(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_10(self, mock_closure, mock_kb, mock_finish_session, mock_update_ticket, mock_issue, mock_get_session):
        # Setup: score 10, current_question 10, is_active True, base ticket 100
        mock_get_session.return_value = (10, 10, True, 100)
        mock_issue.side_effect = [101, 102, 103]
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        # Check bonus tickets issued
        self.assertEqual(mock_issue.call_count, 3)
        mock_update_ticket.assert_called_with(100, "completed", 10)

        # Check message sent
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("10/10", kwargs['text'])
        self.assertIn("№00101", kwargs['text'])
        self.assertIn("№00102", kwargs['text'])
        self.assertIn("№00103", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_7(self, mock_closure, mock_kb, mock_finish_session, mock_update_ticket, mock_issue, mock_get_session):
        # Setup: score 7, current_question 10, is_active True, base ticket 200
        mock_get_session.return_value = (7, 10, True, 200)
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        # Check no bonus tickets issued
        mock_issue.assert_not_called()
        mock_update_ticket.assert_called_with(200, "completed", 7)

        # Check message sent
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("7/10", kwargs['text'])
        self.assertIn("Бонусных билетов не начислено", kwargs['text'])

if __name__ == '__main__':
    unittest.main()
