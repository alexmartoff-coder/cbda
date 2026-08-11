import asyncio
from keyboards.menu import get_main_menu_keyboard
from tests.seed_test_data import seed_data
import sqlite3
from db.db import DB_PATH
from datetime import datetime, timezone, timedelta
import utils.time_utils

# Mock get_moscow_now to a date before the April 10, 2026 deadline
utils.time_utils.get_moscow_now = lambda: datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))

async def test_progress():
    # 1. Reset database closure state
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM settings WHERE key = 'is_closed'")
    cursor.execute("DELETE FROM settings WHERE key = 'is_closure_recorded'")
    cursor.execute("DELETE FROM tickets")
    conn.commit()
    conn.close()

    # 2. Seed exactly 2495 tickets
    await seed_data(2495)

    # 3. Test progress rendering
    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")
    if "2495" in progress:
        print("✅ SUCCESS: Progress reflects 2495 tickets.")
    else:
        print("❌ FAILURE: Progress does NOT reflect 2495 tickets.")
        raise AssertionError("Progress does not reflect 2495 tickets")

if __name__ == "__main__":
    asyncio.run(test_progress())
