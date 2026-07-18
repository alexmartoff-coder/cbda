import asyncio
import aiosqlite
from keyboards.menu import get_main_menu_keyboard
from db.db import DB_PATH, mark_rules_accepted

async def test_progress():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username, full_name, accepted_rules) VALUES (228592391, 'testuser', 'Test User', 1)", ())
        await db.commit()
    await mark_rules_accepted(228592391)

    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")
    if "2495" in progress:
        print("✅ SUCCESS: Progress reflects 2495 tickets.")
    else:
        print("❌ FAILURE: Progress does NOT reflect 2495 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
