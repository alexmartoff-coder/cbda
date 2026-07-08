import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from handlers.quiz import finish_quiz_logic

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_bonus_10_correct(self, mock_closure, mock_kb, mock_finish_session, mock_update, mock_issue, mock_session):
        # score = 10 -> +3 tickets
        mock_session.return_value = (10, 0, True, 1) # score, current_question, is_active, ticket_number
        mock_issue.side_effect = [101, 102, 103]
        mock_kb.return_value = (MagicMock(), "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 123)

        self.assertEqual(mock_issue.call_count, 3)
        mock_issue.assert_any_call(123, "bonus", status='completed')

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_bonus_9_correct(self, mock_closure, mock_kb, mock_finish_session, mock_update, mock_issue, mock_session):
        # score = 9 -> +2 tickets
        mock_session.return_value = (9, 0, True, 1)
        mock_issue.side_effect = [101, 102]
        mock_kb.return_value = (MagicMock(), "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 123)

        self.assertEqual(mock_issue.call_count, 2)

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_bonus_8_correct(self, mock_closure, mock_kb, mock_finish_session, mock_update, mock_issue, mock_session):
        # score = 8 -> +1 ticket
        mock_session.return_value = (8, 0, True, 1)
        mock_issue.return_value = 101
        mock_kb.return_value = (MagicMock(), "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 123)

        self.assertEqual(mock_issue.call_count, 1)

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    async def test_bonus_7_correct(self, mock_closure, mock_kb, mock_finish_session, mock_update, mock_issue, mock_session):
        # score = 7 -> 0 bonus
        mock_session.return_value = (7, 0, True, 1)
        mock_kb.return_value = (MagicMock(), "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 123)

        self.assertEqual(mock_issue.call_count, 0)

if __name__ == '__main__':
    unittest.main()
