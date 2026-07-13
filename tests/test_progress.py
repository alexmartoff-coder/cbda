import asyncio
import os
from keyboards.menu import get_main_menu_keyboard
from db.db import init_db, issue_ticket, DB_PATH
from config import TICKET_LIMIT, INITIAL_FAKE_TICKETS

async def test_progress():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    await init_db()

    user_id = 999
    # Initial state: should show INITIAL_FAKE_TICKETS
    kb, progress = await get_main_menu_keyboard(user_id)
    print(f"Initial progress: {progress}")
    assert f"<b>{INITIAL_FAKE_TICKETS}</b>" in progress
    assert f"из <b>{TICKET_LIMIT}</b>" in progress

    # Issue some tickets
    for _ in range(10):
        await issue_ticket(user_id, 'paid', status='completed')

    kb, progress = await get_main_menu_keyboard(user_id)
    print(f"Progress after 10 tickets: {progress}")
    # total_real is 10. max(741, 10) is 741.
    assert f"<b>{INITIAL_FAKE_TICKETS}</b>" in progress

    # Issue more tickets to exceed 741
    async def issue_many(n):
        for _ in range(n):
            await issue_ticket(user_id, 'paid', status='completed')

    await issue_many(740) # Total 750
    kb, progress = await get_main_menu_keyboard(user_id)
    print(f"Progress after 750 tickets: {progress}")
    assert "<b>750</b>" in progress

    print("✅ Progress test passed!")

if __name__ == "__main__":
    asyncio.run(test_progress())
