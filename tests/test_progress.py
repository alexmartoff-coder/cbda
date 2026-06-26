import asyncio
from keyboards.menu import get_main_menu_keyboard
from db.db import init_db
import os

async def test_progress():
    # Setup dummy DB
    if os.path.exists("database/bot_database.db"):
        os.remove("database/bot_database.db")
    await init_db()

    # User with 0 tickets (should see 741 / 2500)
    kb, progress = await get_main_menu_keyboard(12345)
    print(f"DEBUG: Progress text is: \n{progress}")
    if "741" in progress and "2500" in progress:
        print("✅ SUCCESS: Progress reflects 741/2500 tickets.")
    else:
        print("❌ FAILURE: Progress does NOT reflect 741/2500 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
