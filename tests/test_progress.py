import asyncio
from keyboards.menu import get_main_menu_keyboard

async def test_progress():
    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")
    if "2495" in progress or "741" in progress or "2500" in progress:
        print("✅ SUCCESS: Progress reflects correct ticket count.")
    else:
        print("❌ FAILURE: Progress does NOT reflect correct ticket count.")

if __name__ == "__main__":
    asyncio.run(test_progress())
