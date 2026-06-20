import asyncio
from keyboards.menu import get_main_menu_keyboard

async def test_progress():
    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")
    if "3495" in progress:
        print("✅ SUCCESS: Progress reflects 3495 tickets.")
    else:
        print("❌ FAILURE: Progress does NOT reflect 3495 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
