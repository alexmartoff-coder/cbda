import asyncio
import os
from db.db import init_db, get_total_tickets_count, check_and_trigger_closure, is_collection_closed, issue_ticket
from aiogram import Bot
from unittest.mock import AsyncMock

async def test_real_db_flow():
    if os.path.exists("database/bot_database.db"):
        os.remove("database/bot_database.db")

    await init_db()

    bot = AsyncMock()

    # 1. Initial state
    count = await get_total_tickets_count()
    print(f"Initial tickets: {count}")
    closed = await is_collection_closed()
    print(f"Is closed: {closed}")

    # 2. Issue tickets until limit
    from config import TICKET_LIMIT
    for i in range(TICKET_LIMIT):
        await issue_ticket(12345, 'base', status='completed')

    count = await get_total_tickets_count()
    print(f"Tickets after issuance: {count}")

    # 3. Trigger closure
    await check_and_trigger_closure(bot)

    closed = await is_collection_closed()
    print(f"Is closed after trigger: {closed}")

    if closed:
        print("✅ SUCCESS: Collection closed at limit.")
    else:
        print("❌ FAILURE: Collection NOT closed at limit.")

    # Give some time for background tasks
    await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_real_db_flow())
