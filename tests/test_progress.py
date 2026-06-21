import asyncio
from keyboards.menu import get_main_menu_keyboard
from db.db import init_db

async def test_progress():
    await init_db()
    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")
    if "741" in progress and "2500" in progress:
        print("✅ SUCCESS: Progress reflects 741 floor and 2500 limit.")
    else:
        print("❌ FAILURE: Progress does NOT reflect expectations.")

if __name__ == "__main__":
    asyncio.run(test_progress())
