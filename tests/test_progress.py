import asyncio
from keyboards.menu import get_main_menu_keyboard
from unittest.mock import patch

async def test_progress():
    # Mock total tickets count to 1000
    with patch('db.db.get_total_tickets_count', return_value=1000):
        with patch('db.db.get_user_ticket_counts', return_value=(5, 0)):
            # We need to patch it in both places it might be used
            with patch('keyboards.menu.get_total_tickets_count', return_value=1000):
                with patch('db.db.is_collection_closed', return_value=False):
                    with patch('db.db.has_accepted_rules', return_value=True):
                        kb, progress = await get_main_menu_keyboard(12345)
                        print(f"DEBUG: Progress text is: \n{progress}")
                        # 1000 total tickets. INITIAL_FAKE_TICKETS=741. Max(741, 1000) = 1000.
                        if "1000" in progress:
                            print("✅ SUCCESS: Progress reflects 1000 tickets.")
                        else:
                            print("❌ FAILURE: Progress does NOT reflect 1000 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
