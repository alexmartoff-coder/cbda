import asyncio
from unittest.mock import patch, AsyncMock
from keyboards.menu import get_main_menu_keyboard
from config import TICKET_LIMIT, INITIAL_FAKE_TICKETS

async def test_progress():
    user_id = 228592391

    # Mocking DB calls
    with patch('database.db.has_accepted_rules', new_callable=AsyncMock) as mock_rules, \
         patch('keyboards.menu.is_collection_closed', new_callable=AsyncMock) as mock_closed, \
         patch('keyboards.menu.get_total_tickets_count', new_callable=AsyncMock) as mock_count, \
         patch('keyboards.menu.is_final_active', new_callable=AsyncMock) as mock_final:

        mock_rules.return_value = True
        mock_closed.return_value = False
        mock_count.return_value = 0
        mock_final.return_value = False

        kb, progress = await get_main_menu_keyboard(user_id)
        print(f"DEBUG: Progress text is: \n{progress}")

        expected_start = f"📊 Сбор билетов: {INITIAL_FAKE_TICKETS} из {TICKET_LIMIT}"
        if progress.startswith(expected_start):
            print(f"✅ SUCCESS: Progress reflects {INITIAL_FAKE_TICKETS} tickets when real is 0.")
        else:
            print(f"❌ FAILURE: Progress text '{progress}' does not start with '{expected_start}'.")

        mock_count.return_value = 1000
        kb, progress = await get_main_menu_keyboard(user_id)
        print(f"DEBUG: Progress text is: \n{progress}")

        expected_start = f"📊 Сбор билетов: 1000 из {TICKET_LIMIT}"
        if progress.startswith(expected_start):
            print("✅ SUCCESS: Progress reflects 1000 tickets when real is 1000.")
        else:
            print(f"❌ FAILURE: Progress text '{progress}' does not start with '{expected_start}'.")

if __name__ == "__main__":
    asyncio.run(test_progress())
