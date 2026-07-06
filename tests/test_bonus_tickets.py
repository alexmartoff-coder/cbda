import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from handlers.quiz import finish_quiz_logic
from aiogram.fsm.context import FSMContext

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('db.db.issue_ticket')
    async def test_bonus_issuance_10_correct(self, mock_issue, mock_kb, mock_closure, mock_finish, mock_update, mock_session):
        # Setup: 10 correct answers
        mock_session.return_value = (10, 10, True, 100) # score, current_q, is_active, ticket_num
        mock_kb.return_value = (MagicMock(), "progress")
        mock_issue.side_effect = [101, 102, 103] # Three bonus tickets

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        # Verify 3 bonus tickets were issued
        self.assertEqual(mock_issue.call_count, 3)
        for call in mock_issue.call_args_list:
            self.assertEqual(call[0][1], 'bonus')
            self.assertEqual(call[1]['status'], 'completed')

        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("Всего билетов за эту попытку: <b>4</b>", kwargs['text'])
        self.assertIn("+3", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('db.db.issue_ticket')
    async def test_bonus_issuance_9_correct(self, mock_issue, mock_kb, mock_closure, mock_finish, mock_update, mock_session):
        # Setup: 9 correct answers
        mock_session.return_value = (9, 10, True, 100)
        mock_kb.return_value = (MagicMock(), "progress")
        mock_issue.side_effect = [101, 102] # Two bonus tickets

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        self.assertEqual(mock_issue.call_count, 2)
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("Всего билетов за эту попытку: <b>3</b>", kwargs['text'])
        self.assertIn("+2", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('db.db.issue_ticket')
    async def test_bonus_issuance_8_correct(self, mock_issue, mock_kb, mock_closure, mock_finish, mock_update, mock_session):
        # Setup: 8 correct answers
        mock_session.return_value = (8, 10, True, 100)
        mock_kb.return_value = (MagicMock(), "progress")
        mock_issue.return_value = 101 # One bonus ticket

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        self.assertEqual(mock_issue.call_count, 1)
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("Всего билетов за эту попытку: <b>2</b>", kwargs['text'])
        self.assertIn("+1", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    @patch('db.db.issue_ticket')
    async def test_no_bonus_tickets(self, mock_issue, mock_kb, mock_closure, mock_finish, mock_update, mock_session):
        # Setup: 7 correct answers
        mock_session.return_value = (7, 10, True, 100)
        mock_kb.return_value = (MagicMock(), "progress")

        bot = AsyncMock()
        state = AsyncMock(spec=FSMContext)
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        self.assertEqual(mock_issue.call_count, 0)
        bot.send_message.assert_called_once()
        args, kwargs = bot.send_message.call_args
        self.assertIn("Всего билетов за эту попытку: <b>1</b>", kwargs['text'])
        self.assertNotIn("+", kwargs['text'])

if __name__ == '__main__':
    unittest.main()
