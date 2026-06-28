import asyncio
from unittest.mock import patch, AsyncMock
from keyboards.menu import get_main_menu_keyboard
from config import INITIAL_FAKE_TICKETS, TICKET_LIMIT

async def test_progress():
    # Test with real_total < INITIAL_FAKE_TICKETS
    with patch('keyboards.menu.get_total_tickets_count', new_callable=AsyncMock) as mock_total, \
         patch('keyboards.menu.is_collection_closed', new_callable=AsyncMock) as mock_closed, \
         patch('db.db.has_accepted_rules', new_callable=AsyncMock) as mock_rules, \
         patch('db.db.get_user_ticket_counts', new_callable=AsyncMock) as mock_user_counts:

        mock_total.return_value = 100
        mock_closed.return_value = False
        mock_rules.return_value = True
        mock_user_counts.return_value = (0, 0)

        kb, progress = await get_main_menu_keyboard(228592391)
        print(f"DEBUG (Low real total): \n{progress}")
        if str(INITIAL_FAKE_TICKETS) in progress:
            print(f"✅ SUCCESS: Progress reflects psychological floor {INITIAL_FAKE_TICKETS}")
        else:
            print(f"❌ FAILURE: Progress does NOT reflect floor {INITIAL_FAKE_TICKETS}")

    # Test with real_total > INITIAL_FAKE_TICKETS
    with patch('keyboards.menu.get_total_tickets_count', new_callable=AsyncMock) as mock_total, \
         patch('keyboards.menu.is_collection_closed', new_callable=AsyncMock) as mock_closed, \
         patch('db.db.has_accepted_rules', new_callable=AsyncMock) as mock_rules, \
         patch('db.db.get_user_ticket_counts', new_callable=AsyncMock) as mock_user_counts:

        real_total = INITIAL_FAKE_TICKETS + 100
        mock_total.return_value = real_total
        mock_closed.return_value = False
        mock_rules.return_value = True
        mock_user_counts.return_value = (0, 0)

        kb, progress = await get_main_menu_keyboard(228592391)
        print(f"DEBUG (High real total): \n{progress}")
        if str(real_total) in progress:
            print(f"✅ SUCCESS: Progress reflects real total {real_total}")
        else:
            print(f"❌ FAILURE: Progress does NOT reflect real total {real_total}")

if __name__ == "__main__":
    asyncio.run(test_progress())
