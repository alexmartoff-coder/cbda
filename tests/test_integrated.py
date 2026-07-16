import asyncio
import os
from db.db import init_db, get_total_tickets_count, check_and_trigger_closure, is_collection_closed, issue_ticket
from keyboards.menu import get_main_menu_keyboard
from aiogram import Bot
from unittest.mock import AsyncMock

async def test_progress_and_closure():
    if os.path.exists("database/bot_database.db"):
        os.remove("database/bot_database.db")

    await init_db()
    bot = AsyncMock()

    # 1. Test floor (741)
    kb, progress = await get_main_menu_keyboard(123)
    print(f"Progress (0 tickets): {progress}")
    if "741" in progress:
        print("✅ SUCCESS: Floor 741 working.")
    else:
        print("❌ FAILURE: Floor 741 NOT working.")

    # 2. Test actual tickets > 741
    for i in range(800):
        await issue_ticket(123, 'base', status='completed')

    kb, progress = await get_main_menu_keyboard(123)
    print(f"Progress (800 tickets): {progress}")
    if "800" in progress:
        print("✅ SUCCESS: Progress reflects 800 tickets.")
    else:
        print("❌ FAILURE: Progress does NOT reflect 800 tickets.")

    # 3. Test closure at 2500
    for i in range(1700):
        await issue_ticket(123, 'base', status='completed')

    await check_and_trigger_closure(bot)
    closed = await is_collection_closed()
    print(f"Is closed at 2500: {closed}")

    kb, progress = await get_main_menu_keyboard(123)
    print(f"Progress (2500 tickets): {progress}")
    if "2500" in progress:
        print("✅ SUCCESS: Progress reflects 2500 tickets.")

    if closed:
        print("✅ SUCCESS: Closure working.")

if __name__ == "__main__":
    asyncio.run(test_progress_and_closure())
