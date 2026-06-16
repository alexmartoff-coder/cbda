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
    async def test_scoring_10_correct(self, mock_closure, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        # Setup: score 10, base ticket 100
        mock_session.return_value = (10, 0, True, 100)
        mock_issue.side_effect = [101, 102, 103]
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        # Check if 3 bonus tickets were issued
        self.assertEqual(mock_issue.call_count, 3)
        args, kwargs = bot.send_message.call_args
        self.assertIn("Начислено бонусных билетов: <b>+3</b>", kwargs['text'])
        self.assertIn("№00100, №00101, №00102, №00103", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_9_correct(self, mock_closure, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        # Setup: score 9
        mock_session.return_value = (9, 0, True, 200)
        mock_issue.side_effect = [201, 202]
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        self.assertEqual(mock_issue.call_count, 2)
        args, kwargs = bot.send_message.call_args
        self.assertIn("Начислено бонусных билетов: <b>+2</b>", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_8_correct(self, mock_closure, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        # Setup: score 8
        mock_session.return_value = (8, 0, True, 300)
        mock_issue.side_effect = [301]
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        self.assertEqual(mock_issue.call_count, 1)
        args, kwargs = bot.send_message.call_args
        self.assertIn("Начислено бонусных билетов: <b>+1</b>", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_7_correct(self, mock_closure, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        # Setup: score 7
        mock_session.return_value = (7, 0, True, 400)
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        self.assertEqual(mock_issue.call_count, 0)
        args, kwargs = bot.send_message.call_args
        self.assertIn("Начислено бонусных билетов: <b>+0</b>", kwargs['text'])

if __name__ == '__main__':
    unittest.main()
