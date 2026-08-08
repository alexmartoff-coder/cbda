import asyncio
from keyboards.menu import get_main_menu_keyboard
from db.db import add_user, mark_rules_accepted, init_db

async def test_progress():
    await init_db()
    uid = 228592391
    await add_user(uid, "test_user", "Test User")
    await mark_rules_accepted(uid)

    kb, progress = await get_main_menu_keyboard(uid)
    print(f"DEBUG: Progress text is: \n{progress}")
    if "2500" in progress:
        print("✅ SUCCESS: Progress reflects 2500 tickets limit.")
    else:
        print("❌ FAILURE: Progress does NOT reflect 2500 tickets limit.")

if __name__ == "__main__":
    asyncio.run(test_progress())
