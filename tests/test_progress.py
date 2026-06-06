import asyncio
from keyboards.menu import get_main_menu_keyboard
from config import TICKET_LIMIT

async def test_progress():
    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")
    if f"{TICKET_LIMIT} из {TICKET_LIMIT}" in progress:
        print("✅ SUCCESS: Progress reflects full tickets.")
    else:
        print("❌ FAILURE: Progress does NOT reflect full tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
