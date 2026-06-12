import asyncio
import os
import aiosqlite
from keyboards.menu import get_main_menu_keyboard
from database.db import init_db, DB_PATH

async def test_progress():
    # Ensure DB is initialized
    await init_db()

    # Add a user to make get_user_ticket_counts work
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)", (228592391, 'testuser', 'Test User'))
        await db.commit()

    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")

    # We set TICKET_LIMIT to 2500, and INITIAL_FAKE_TICKETS is 741.
    # Total real tickets is likely 0 if it's a fresh DB.
    # So progress should show 741 out of 2500.
    if "741" in progress and "2500" in progress:
        print("✅ SUCCESS: Progress reflects 741/2500 tickets.")
    else:
        print(f"❌ FAILURE: Progress does NOT reflect expected values. Got: {progress}")

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    asyncio.run(test_progress())
