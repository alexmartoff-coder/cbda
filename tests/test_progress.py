import asyncio
from keyboards.menu import get_main_menu_keyboard
from database.db import init_db, add_user, issue_ticket, close_collection
import os
from config import INITIAL_FAKE_TICKETS, TICKET_LIMIT

async def test_progress():
    db_path = "bot_database.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    await init_db()
    user_id = 12345
    await add_user(user_id, "testuser", "Test User")

    # Initial state
    kb, progress = await get_main_menu_keyboard(user_id)
    print(f"Initial progress: {progress}")
    # Should show INITIAL_FAKE_TICKETS (741)
    if str(INITIAL_FAKE_TICKETS) not in progress:
        print(f"FAILED: Initial progress should show {INITIAL_FAKE_TICKETS}")

    # Issue some tickets
    for _ in range(10):
        await issue_ticket(user_id, "base")

    kb, progress = await get_main_menu_keyboard(user_id)
    print(f"Progress after 10 tickets: {progress}")
    # Since 10 < 741, it should still show 741
    if str(INITIAL_FAKE_TICKETS) not in progress:
         print(f"FAILED: Progress should still show {INITIAL_FAKE_TICKETS}")

    # Issue more tickets to exceed 741
    for _ in range(800):
        await issue_ticket(user_id, "base")

    kb, progress = await get_main_menu_keyboard(user_id)
    print(f"Progress after 810 tickets: {progress}")
    if "810" not in progress:
        print(f"FAILED: Progress should show 810")

    # Close collection
    await close_collection()
    kb, progress = await get_main_menu_keyboard(user_id)
    print(f"Progress after closure: {progress}")
    if "Приём заявок завершён" not in progress:
        print("FAILED: Progress should indicate closure")

    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    asyncio.run(test_progress())
