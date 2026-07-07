import asyncio
from unittest.mock import AsyncMock, patch
import keyboards.menu
from config import TICKET_LIMIT, INITIAL_FAKE_TICKETS

async def test_progress():
    # Mocking functions as they are imported in keyboards.menu
    # Note: get_main_menu_keyboard does "from db.db import has_accepted_rules, get_user_ticket_counts"
    # inside the function. This is tricky to patch.
    # Actually, in keyboards/menu.py:
    # from db.db import is_collection_closed, has_user_used_free_attempt, get_total_tickets_count

    with patch('keyboards.menu.get_total_tickets_count', return_value=100), \
         patch('keyboards.menu.is_collection_closed', return_value=False), \
         patch('keyboards.menu.has_accepted_rules', return_value=True), \
         patch('keyboards.menu.get_user_ticket_counts', return_value=(0, 0)):

        kb, progress = await keyboards.menu.get_main_menu_keyboard(12345)
        print(f"DEBUG: Progress text is: \n{progress}")

        # 100 real tickets -> display_count should be max(741, 100) = 741
        if str(INITIAL_FAKE_TICKETS) in progress:
            print(f"✅ SUCCESS: Progress reflects {INITIAL_FAKE_TICKETS} tickets.")
        else:
            print(f"❌ FAILURE: Progress does NOT reflect {INITIAL_FAKE_TICKETS} tickets.")

    with patch('keyboards.menu.get_total_tickets_count', return_value=2000), \
         patch('keyboards.menu.is_collection_closed', return_value=False), \
         patch('keyboards.menu.has_accepted_rules', return_value=True), \
         patch('keyboards.menu.get_user_ticket_counts', return_value=(0, 0)):

        kb, progress = await keyboards.menu.get_main_menu_keyboard(12345)
        print(f"DEBUG: Progress text is: \n{progress}")

        # 2000 real tickets -> display_count should be 2000
        if "2000" in progress:
            print("✅ SUCCESS: Progress reflects 2000 tickets.")
        else:
            print("❌ FAILURE: Progress does NOT reflect 2000 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
