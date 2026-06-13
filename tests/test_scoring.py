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
    async def test_scoring_10(self, mock_closure, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        # 10 correct answers -> +3 bonus
        mock_session.return_value = (10, 10, True, 100) # score, current_q, is_active, t_num
        mock_issue.side_effect = [101, 102, 103]
        mock_kb.return_value = (None, "Progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 123)

        self.assertEqual(mock_issue.call_count, 3)
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("Бонусные билеты (3 шт.): №00101, №00102, №00103", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_9(self, mock_closure, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        # 9 correct answers -> +2 bonus
        mock_session.return_value = (9, 10, True, 200)
        mock_issue.side_effect = [201, 202]
        mock_kb.return_value = (None, "Progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 123)

        self.assertEqual(mock_issue.call_count, 2)
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("Бонусные билеты (2 шт.): №00201, №00202", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('database.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_scoring_7(self, mock_closure, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        # 7 correct answers -> 0 bonus
        mock_session.return_value = (7, 10, True, 300)
        mock_kb.return_value = (None, "Progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 123)

        self.assertEqual(mock_issue.call_count, 0)
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("Бонусных билетов за этот квиз не получено", kwargs['text'])

if __name__ == '__main__':
    unittest.main()
