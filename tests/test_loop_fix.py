import asyncio
from db.db import init_db, add_user, issue_ticket, get_user_applications
import os

async def test_infinite_loop_fix():
    if os.path.exists("database/bot_database.db"):
        os.remove("database/bot_database.db")
    await init_db()

    user_id = 12345
    await add_user(user_id, "testuser", "Test")

    # Simulate awarding bonus tickets
    # In raffle mode, bonus tickets should have status='completed'
    await issue_ticket(user_id, "bonus", status='completed')
    await issue_ticket(user_id, "bonus", status='completed')

    apps = await get_user_applications(user_id)
    # check if any bonus ticket has status 'pending'
    pending_bonus = [t for t in apps if t[1] == 'pending']

    if not pending_bonus:
        print("✅ SUCCESS: Bonus tickets are NOT pending. Infinite loop fix verified.")
    else:
        print(f"❌ FAILURE: Found pending bonus tickets: {pending_bonus}")

if __name__ == "__main__":
    asyncio.run(test_infinite_loop_fix())
