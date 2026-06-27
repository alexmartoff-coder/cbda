import asyncio
from unittest.mock import patch
from keyboards.menu import get_main_menu_keyboard

async def test_progress():
    # Test with 0 real tickets (should show INITIAL_FAKE_TICKETS = 741)
    with patch('keyboards.menu.get_total_tickets_count', return_value=0):
        kb, progress = await get_main_menu_keyboard(123)
        print(f"DEBUG (0 tickets): Progress text is: \n{progress}")
        if "741" in progress:
            print("✅ SUCCESS: Progress reflects INITIAL_FAKE_TICKETS.")
        else:
            print("❌ FAILURE: Progress does NOT reflect INITIAL_FAKE_TICKETS.")

    # Test with 1500 real tickets
    with patch('keyboards.menu.get_total_tickets_count', return_value=1500):
        kb, progress = await get_main_menu_keyboard(123)
        print(f"DEBUG (1500 tickets): Progress text is: \n{progress}")
        if "1500" in progress:
            print("✅ SUCCESS: Progress reflects 1500 tickets.")
        else:
            print("❌ FAILURE: Progress does NOT reflect 1500 tickets.")

    # Test with TICKET_LIMIT (2500)
    with patch('keyboards.menu.get_total_tickets_count', return_value=2500):
        kb, progress = await get_main_menu_keyboard(123)
        print(f"DEBUG (2500 tickets): Progress text is: \n{progress}")
        if "2500" in progress:
            print("✅ SUCCESS: Progress reflects TICKET_LIMIT.")
        else:
            print("❌ FAILURE: Progress does NOT reflect TICKET_LIMIT.")

if __name__ == "__main__":
    asyncio.run(test_progress())
