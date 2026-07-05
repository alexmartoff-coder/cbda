import asyncio
import unittest
from unittest.mock import AsyncMock, patch
from handlers.quiz import finish_quiz_logic

class TestBonusTickets(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.quiz.get_quiz_session')
    @patch('db.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_tickets_10_score(self, mock_kb, mock_closure, mock_finish_session, mock_update_res, mock_issue, mock_get_session):
        # 10/10 score -> +3 bonus
        mock_get_session.return_value = (10, 10, True, 100) # score, current_q, is_active, t_num
        mock_issue.side_effect = [101, 102, 103] # Issued bonus ticket numbers
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        # Should issue 3 bonus tickets
        self.assertEqual(mock_issue.call_count, 3)
        mock_issue.assert_any_call(user_id, "bonus", status='completed')

        # Verify final message
        args, kwargs = bot.send_message.call_args
        self.assertIn("Ты получаешь <b>+3 бонусных билета(ов)</b>", kwargs['text'])
        self.assertIn("№00101, №00102, №00103", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('db.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_tickets_9_score(self, mock_kb, mock_closure, mock_finish_session, mock_update_res, mock_issue, mock_get_session):
        # 9/10 score -> +2 bonus
        mock_get_session.return_value = (9, 10, True, 100)
        mock_issue.side_effect = [101, 102]
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        self.assertEqual(mock_issue.call_count, 2)
        args, kwargs = bot.send_message.call_args
        self.assertIn("Ты получаешь <b>+2 бонусных билета(ов)</b>", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('db.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_tickets_8_score(self, mock_kb, mock_closure, mock_finish_session, mock_update_res, mock_issue, mock_get_session):
        # 8/10 score -> +1 bonus
        mock_get_session.return_value = (8, 10, True, 100)
        mock_issue.side_effect = [101]
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        self.assertEqual(mock_issue.call_count, 1)
        args, kwargs = bot.send_message.call_args
        self.assertIn("Ты получаешь <b>+1 бонусных билета(ов)</b>", kwargs['text'])

    @patch('handlers.quiz.get_quiz_session')
    @patch('db.db.issue_ticket')
    @patch('handlers.quiz.update_ticket_result')
    @patch('handlers.quiz.finish_quiz_session')
    @patch('handlers.quiz.check_and_trigger_closure')
    @patch('handlers.quiz.get_main_menu_keyboard')
    async def test_bonus_tickets_low_score(self, mock_kb, mock_closure, mock_finish_session, mock_update_res, mock_issue, mock_get_session):
        # 7/10 score -> 0 bonus
        mock_get_session.return_value = (7, 10, True, 100)
        mock_kb.return_value = (None, "progress")

        bot = AsyncMock()
        state = AsyncMock()
        user_id = 123

        await finish_quiz_logic(bot, state, user_id)

        self.assertEqual(mock_issue.call_count, 0)
        args, kwargs = bot.send_message.call_args
        self.assertIn("недостаточно для бонусов", kwargs['text'])

if __name__ == '__main__':
    unittest.main()
