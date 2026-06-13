import asyncio
from keyboards import menu
from unittest.mock import patch, AsyncMock, MagicMock
from config import TICKET_LIMIT, INITIAL_FAKE_TICKETS

async def test_progress():
    # Test 1: Empty DB, should show floor (741)
    # We mock everything so that get_main_menu_keyboard hits the "if not effective_closed" block
    with patch('keyboards.menu.is_collection_closed', new_callable=AsyncMock) as mock_closed, \
         patch('keyboards.menu.is_final_active', new_callable=AsyncMock) as mock_final_active, \
         patch('database.db_final.get_final_times', new_callable=AsyncMock) as mock_times, \
         patch('database.db.get_paid_tickets_count', new_callable=AsyncMock) as mock_paid, \
         patch('database.db.get_user_ticket_counts', new_callable=AsyncMock) as mock_user, \
         patch('database.db.has_accepted_rules', new_callable=AsyncMock) as mock_rules, \
         patch('aiosqlite.connect') as mock_connect:

        mock_closed.return_value = False
        mock_final_active.return_value = False
        mock_times.return_value = {} # Not None, but empty dict
        mock_paid.return_value = 0
        mock_user.return_value = (0, 0)
        mock_rules.return_value = True

        mock_db = MagicMock()
        mock_connect.return_value.__aenter__.return_value = mock_db
        mock_context = MagicMock()
        mock_db.execute.return_value = mock_context
        mock_cursor = AsyncMock()
        mock_context.__aenter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (0,)

        kb, progress = await menu.get_main_menu_keyboard(123)
        print(f"DEBUG: Progress text (Empty DB): \n{progress}")
        expected_start = INITIAL_FAKE_TICKETS
        if f"{expected_start} из {TICKET_LIMIT}" in progress:
            print("✅ SUCCESS: Progress reflects floor.")
        else:
            print("❌ FAILURE: Progress does NOT reflect floor.")

if __name__ == "__main__":
    asyncio.run(test_progress())
