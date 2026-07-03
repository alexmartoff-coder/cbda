import asyncio
from keyboards.menu import get_main_menu_keyboard
from config import TICKET_LIMIT

async def test_progress():
    # Mocking user ID to avoid DB lookups if possible, but get_main_menu_keyboard does lookups.
    # We need a dummy DB or mock the DB calls.
    # Let's just run it and see if it crashes or returns expected 2500 in text.
    try:
        kb, progress = await get_main_menu_keyboard(None)
        print(f"DEBUG: Progress text is: \n{progress}")
        limit_str = str(TICKET_LIMIT)
        if limit_str in progress:
            print(f"✅ SUCCESS: Progress reflects {limit_str} tickets.")
        else:
            print(f"❌ FAILURE: Progress does NOT reflect {limit_str} tickets.")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_progress())
