import asyncio
import aiosqlite
from keyboards.menu import get_main_menu_keyboard
from db.db import init_db, issue_ticket, DB_PATH
import os

async def test_progress():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    await init_db()
    user_id = 228592391

    # 1. Total tickets < 741 (fake floor)
    kb, progress = await get_main_menu_keyboard(user_id)
    print(f"DEBUG (0 tickets): \n{progress}")
    assert "741" in progress

    # 2. Add some tickets but still < 2500
    for _ in range(10):
        await issue_ticket(user_id, "paid")

    kb, progress = await get_main_menu_keyboard(user_id)
    print(f"DEBUG (10 tickets): \n{progress}")
    assert "741" in progress # because max(741, 10) = 741

    # 3. Reach limit
    async with aiosqlite.connect(DB_PATH) as db:
        # Manually insert many tickets to reach limit
        batch = [(user_id, n, "paid", "completed") for n in range(100, 2600)]
        await db.executemany("INSERT INTO tickets (user_id, ticket_number, type, status) VALUES (?, ?, ?, ?)", batch)
        await db.commit()

    kb, progress = await get_main_menu_keyboard(user_id)
    print(f"DEBUG (2500 tickets): \n{progress}")
    assert "2500" in progress
    assert "100%" in progress

    print("Progress test passed!")

if __name__ == "__main__":
    asyncio.run(test_progress())
