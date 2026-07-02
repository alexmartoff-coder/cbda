import asyncio
from keyboards.menu import get_main_menu_keyboard
from config import TICKET_LIMIT

async def test_progress():
    # Since we are using an empty DB, we expect the INITIAL_FAKE_TICKETS to be shown
    from config import INITIAL_FAKE_TICKETS
    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")
    if str(INITIAL_FAKE_TICKETS) in progress and str(TICKET_LIMIT) in progress:
        print(f"✅ SUCCESS: Progress reflects {INITIAL_FAKE_TICKETS} (initial fake) and limit {TICKET_LIMIT}.")
    else:
        print(f"❌ FAILURE: Progress does NOT reflect expected values.")

if __name__ == "__main__":
    asyncio.run(test_progress())
