import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from handlers.quiz import finish_quiz_logic

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_tickets_perfect_score(self, mock_kb, mock_closure, mock_finish_session, mock_update, mock_issue, mock_session):
        # 10 correct answers -> should issue 3 bonus tickets
        mock_session.return_value = (10, 10, True, 42) # (score, current_question, is_active, ticket_number)
        mock_issue.side_effect = [101, 102, 103] # sequential ticket numbers
        mock_kb.return_value = (MagicMock(), "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 12345)

        # Verify mock_issue was called exactly 3 times
        self.assertEqual(mock_issue.call_count, 3)
        mock_issue.assert_any_call(12345, "bonus", status="completed")

        # Verify base ticket update
        mock_update.assert_called_once_with(42, "completed", 10)

        # Verify FSM cleared
        state.clear.assert_called_once()

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_tickets_no_bonus(self, mock_kb, mock_closure, mock_finish_session, mock_update, mock_issue, mock_session):
        # 7 correct answers -> should issue 0 bonus tickets
        mock_session.return_value = (7, 10, True, 42)
        mock_kb.return_value = (MagicMock(), "progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 12345)

        # Verify mock_issue was called exactly 0 times
        mock_issue.assert_not_called()

        # Verify base ticket update
        mock_update.assert_called_once_with(42, "completed", 7)

if __name__ == "__main__":
    unittest.main()
