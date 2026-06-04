import asyncio
from keyboards.menu import get_main_menu_keyboard
from config import TICKET_LIMIT

async def test_progress():
    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")
    print(f"DEBUG: TICKET_LIMIT is {TICKET_LIMIT}")
    if "2500" in progress:
        print("✅ SUCCESS: Progress reflects 2500 tickets.")
    else:
        print("❌ FAILURE: Progress does NOT reflect 2500 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
