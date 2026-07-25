import asyncio
import aiosqlite
from keyboards.menu import get_main_menu_keyboard
from db.db import mark_rules_accepted, add_user, init_db

async def test_progress():
    await init_db()
    user_id = 228592391
    await add_user(user_id, "test_user", "Test User")
    await mark_rules_accepted(user_id)

    kb, progress = await get_main_menu_keyboard(user_id)
    print(f"DEBUG: Progress text is: \n{progress}")
    if "741" in progress:
        print("✅ SUCCESS: Progress reflects 741 tickets.")
    else:
        print("❌ FAILURE: Progress does NOT reflect 741 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
