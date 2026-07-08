import asyncio
from keyboards.menu import get_main_menu_keyboard
from config import INITIAL_FAKE_TICKETS, TICKET_LIMIT

async def test_progress():
    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")

    # In the new version, display_count should be max(741, real_total)
    # Since our DB is empty, it should be 741.
    expected_val = str(INITIAL_FAKE_TICKETS)
    if expected_val in progress:
        print(f"✅ SUCCESS: Progress reflects {expected_val} tickets (floor).")
    else:
        print(f"❌ FAILURE: Progress does NOT reflect {expected_val} tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
