import asyncio
from keyboards.menu import get_main_menu_keyboard
from db.db import add_user, mark_rules_accepted

async def test_progress():
    # Add user first so update works
    await add_user(228592391, "test_owner", "Test Owner")
    # Make sure rules are accepted to see the progress bar
    await mark_rules_accepted(228592391)
    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is: \n{progress}")
    if "2500" in progress:
        print("✅ SUCCESS: Progress reflects 2500 tickets.")
    else:
        print("❌ FAILURE: Progress does NOT reflect 2500 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
