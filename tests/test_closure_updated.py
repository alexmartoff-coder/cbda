import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from db.db import check_and_trigger_closure
from config import TICKET_LIMIT

class TestClosure(unittest.IsolatedAsyncioTestCase):
    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_closure_by_tickets(self, mock_now, mock_close, mock_is_closed, mock_count):
        # Setup: TICKET_LIMIT tickets, not closed
        mock_count.return_value = TICKET_LIMIT
        mock_is_closed.side_effect = [False, True] # First check in trigger, second to avoid re-triggering? No, actually is_closed is checked before broadcast recording
        mock_now.return_value.replace.return_value = datetime(2025, 1, 1) # way before deadline

        bot = AsyncMock()

        # We need to mock aiosqlite for the settings check
        with patch('aiosqlite.connect') as mock_db:
            mock_cursor = mock_db.return_value.__aenter__.return_value.execute.return_value.__aenter__.return_value
            mock_cursor.fetchone.return_value = ['0'] # is_closure_recorded = 0

            await check_and_trigger_closure(bot)

        mock_close.assert_called_once()
        bot.send_message.assert_called() # Broadcast + Channel

    @patch('db.db.get_total_tickets_count')
    @patch('db.db.is_collection_closed')
    @patch('db.db.close_collection')
    @patch('db.db.get_moscow_now')
    async def test_no_closure(self, mock_now, mock_close, mock_is_closed, mock_count):
        mock_count.return_value = 100
        mock_is_closed.return_value = False
        mock_now.return_value.replace.return_value = datetime(2025, 1, 1)

        bot = AsyncMock()

        await check_and_trigger_closure(bot)

        mock_close.assert_not_called()

if __name__ == '__main__':
    unittest.main()
