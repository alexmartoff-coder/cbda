import asyncio
from keyboards.menu import get_main_menu_keyboard

async def test_progress():
    # We expect 741 floor if DB is empty
    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")
    if "741" in progress:
        print("✅ SUCCESS: Progress reflects 741 floor.")
    else:
        print("❌ FAILURE: Progress does NOT reflect 741 floor.")

if __name__ == "__main__":
    asyncio.run(test_progress())
