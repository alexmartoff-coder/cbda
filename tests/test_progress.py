import asyncio
from keyboards.menu import get_main_menu_keyboard
from database.db import close_collection

async def test_progress():
    # Simulate closure
    await close_collection()
    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")
    if "Сбор билетов завершён!" in progress:
        print("✅ SUCCESS: Progress reflects closure.")
    else:
        print("❌ FAILURE: Progress does NOT reflect closure.")

if __name__ == "__main__":
    asyncio.run(test_progress())
