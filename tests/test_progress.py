import asyncio
from keyboards.menu import get_main_menu_keyboard
from unittest.mock import patch, AsyncMock

async def test_progress():
    # Mocking database calls to simulate state
    # Important: patch where the functions are IMPORTED in keyboards/menu.py if they are imported using 'from db.db import ...'
    # In menu.py: from db.db import is_collection_closed, get_total_tickets_count, get_paid_tickets_count

    with patch('keyboards.menu.get_total_tickets_count', new_callable=AsyncMock) as mock_total, \
         patch('keyboards.menu.is_collection_closed', new_callable=AsyncMock) as mock_closed, \
         patch('db.db.has_accepted_rules', new_callable=AsyncMock) as mock_rules, \
         patch('db.db.get_user_ticket_counts', new_callable=AsyncMock) as mock_user_tickets:

        # Test Case 1: Low ticket count (should show 741)
        mock_total.return_value = 10
        mock_closed.return_value = False
        mock_rules.return_value = True
        mock_user_tickets.return_value = (0, 0)

        kb, progress = await get_main_menu_keyboard(12345)
        print(f"DEBUG Case 1: Progress text is: \n{progress}")
        if "741" in progress:
            print("✅ SUCCESS: Progress reflects 741 tickets (floor).")
        else:
            print("❌ FAILURE: Progress does NOT reflect 741 tickets.")

        # Test Case 2: Above floor (should show real count)
        mock_total.return_value = 800
        kb, progress = await get_main_menu_keyboard(12345)
        print(f"DEBUG Case 2: Progress text is: \n{progress}")
        if "800" in progress:
            print("✅ SUCCESS: Progress reflects 800 tickets.")
        else:
            print("❌ FAILURE: Progress does NOT reflect 800 tickets.")

        # Test Case 3: Reaching limit
        mock_total.return_value = 2500
        kb, progress = await get_main_menu_keyboard(12345)
        print(f"DEBUG Case 3: Progress text is: \n{progress}")
        if "2500" in progress and "100%" in progress:
            print("✅ SUCCESS: Progress reflects 2500 tickets (100%).")
        else:
            print("❌ FAILURE: Progress does NOT reflect 2500 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
