import asyncio
from keyboards.menu import get_main_menu_keyboard
from database.db import add_user, mark_rules_accepted, DB_PATH
import aiosqlite
import os
from unittest.mock import patch
from datetime import datetime

async def test_progress():
    user_id = 228592391

    # Setup database with some tickets
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    from database.db import init_db
    await init_db()
    await add_user(user_id, 'test', 'test')
    await mark_rules_accepted(user_id)

    async with aiosqlite.connect(DB_PATH) as db:
        # Add 1000 tickets to trigger real count
        batch = [(user_id, i, 'paid', 'issued') for i in range(1, 1001)]
        await db.executemany("INSERT INTO tickets (user_id, ticket_number, type, status) VALUES (?, ?, ?, ?)", batch)
        await db.commit()

    with patch('database.db.get_moscow_now') as mock_now:
        mock_now.return_value = datetime(2026, 4, 1, tzinfo=None) # Before deadline
        kb, progress = await get_main_menu_keyboard(user_id)
        print(f"DEBUG: Progress text is: \n{progress}")

        if "1000" in progress:
            print("✅ SUCCESS: Progress reflects 1000 tickets.")
        else:
            print("❌ FAILURE: Progress does NOT reflect 1000 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
