import unittest
from unittest.mock import AsyncMock, patch
from handlers.quiz import finish_quiz_logic
from aiogram.fsm.context import FSMContext

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.get_total_tickets_count')
    async def test_finish_quiz_bonus_3(self, mock_total, mock_get_session, mock_issue, mock_finish_session, mock_update_res, mock_trigger, mock_menu):
        mock_get_session.return_value = (10, 10, True, 101) # 10/10 score
        mock_issue.side_effect = [102, 103, 104]
        mock_total.return_value = 104
        mock_menu.return_value = (None, "Progress")

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)

        await finish_quiz_logic(bot, state, user_id=12345)

        self.assertEqual(mock_issue.call_count, 3)
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("10/10", kwargs['text'])
        self.assertIn("№00102", kwargs['text'])

    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.issue_ticket')
    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.get_total_tickets_count')
    async def test_finish_quiz_bonus_0(self, mock_total, mock_get_session, mock_issue, mock_finish_session, mock_update_res, mock_trigger, mock_menu):
        mock_get_session.return_value = (5, 10, True, 101) # 5/10 score
        mock_total.return_value = 101
        mock_menu.return_value = (None, "Progress")

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)

        await finish_quiz_logic(bot, state, user_id=12345)

        mock_issue.assert_not_called()
        bot.send_message.assert_called_once()

if __name__ == '__main__':
    unittest.main()
