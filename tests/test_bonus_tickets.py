import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from handlers.quiz import finish_quiz_logic

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_tickets_10_score(self, mock_kb, mock_closure, mock_finish_session, mock_update_result, mock_issue, mock_get_session):
        # Setup: 10 correct answers
        mock_get_session.return_value = (10, 10, True, 123) # score, current_question, is_active, ticket_number
        mock_issue.return_value = 456
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 999)

        # Should issue 3 bonus tickets
        self.assertEqual(mock_issue.call_count, 3)
        mock_issue.assert_any_call(999, "bonus", status='completed')

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_tickets_9_score(self, mock_kb, mock_closure, mock_finish_session, mock_update_result, mock_issue, mock_get_session):
        # Setup: 9 correct answers
        mock_get_session.return_value = (9, 10, True, 123)
        mock_issue.return_value = 456
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 999)

        # Should issue 2 bonus tickets
        self.assertEqual(mock_issue.call_count, 2)

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_tickets_8_score(self, mock_kb, mock_closure, mock_finish_session, mock_update_result, mock_issue, mock_get_session):
        # Setup: 8 correct answers
        mock_get_session.return_value = (8, 10, True, 123)
        mock_issue.return_value = 456
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 999)

        # Should issue 1 bonus ticket
        self.assertEqual(mock_issue.call_count, 1)

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_tickets_low_score(self, mock_kb, mock_closure, mock_finish_session, mock_update_result, mock_issue, mock_get_session):
        # Setup: 7 correct answers
        mock_get_session.return_value = (7, 10, True, 123)
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 999)

        # Should issue 0 bonus tickets
        self.assertEqual(mock_issue.call_count, 0)

if __name__ == '__main__':
    unittest.main()
