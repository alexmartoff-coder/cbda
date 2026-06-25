import asyncio
from keyboards.menu import get_main_menu_keyboard
from db.db import init_db, add_user, issue_ticket, update_ticket_result
import os

async def test_progress():
    # Setup real DB state for testing progress bar
    if os.path.exists("database/bot_database.db"):
        os.remove("database/bot_database.db")
    await init_db()

    user_id = 228592391
    await add_user(user_id, "testuser", "Test User")

    # 741 is initial fake
    # Add 10 paid tickets
    for _ in range(10):
        await issue_ticket(user_id, "paid")

    # All should be completed for simplicity in this test
    # (though the keyboard logic just counts total tickets)

    kb, progress = await get_main_menu_keyboard(user_id)
    print(f"DEBUG: Progress text is: \n{progress}")

    # 741 + 10 = 751
    if "751" in progress:
        print("✅ SUCCESS: Progress reflects 751 tickets (741 fake + 10 real).")
    else:
        print(f"❌ FAILURE: Progress does NOT reflect 751 tickets. Got: {progress}")

    # Test limit reaching
    # Total tickets = 2500
    from config import TICKET_LIMIT
    current_count = 10 # we already have 10
    for _ in range(TICKET_LIMIT - 741 - 10 + 1):
         await issue_ticket(user_id, "paid")

    kb, progress = await get_main_menu_keyboard(user_id)
    # display_count = max(741 + user_paid, real_total)
    # user_paid will be TICKET_LIMIT - 741 + 1. So display_count will be TICKET_LIMIT + 1, then capped to TICKET_LIMIT.
    if str(TICKET_LIMIT) in progress and "100%" in progress:
         print(f"✅ SUCCESS: Progress reflects {TICKET_LIMIT} tickets and 100%.")
    else:
         print(f"❌ FAILURE: Progress does NOT reflect {TICKET_LIMIT} tickets. Got: {progress}")

if __name__ == "__main__":
    asyncio.run(test_progress())
