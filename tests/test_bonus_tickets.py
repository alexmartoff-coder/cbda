import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from handlers.quiz import finish_quiz_logic

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_3_tickets(self, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        mock_session.return_value = (10, 0, True, 100) # Score 10, Ticket 100
        mock_issue.return_value = 101 # Dummy bonus ticket num
        mock_kb.return_value = (None, "Progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 12345)

        self.assertEqual(mock_issue.call_count, 3)
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("+3 бонусных билета", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_0_tickets(self, mock_kb, mock_finish, mock_update, mock_issue, mock_session):
        mock_session.return_value = (5, 0, True, 200) # Score 5
        mock_kb.return_value = (None, "Progress")

        bot = AsyncMock()
        state = AsyncMock()

        await finish_quiz_logic(bot, state, 12345)

        mock_issue.assert_not_called()
        self.assertIn("без бонусов", bot.send_message.call_args[1]['text'])

if __name__ == '__main__':
    unittest.main()
