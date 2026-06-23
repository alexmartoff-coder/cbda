import asyncio
from keyboards import menu
from unittest.mock import patch, AsyncMock

async def test_progress():
    # Mocking at the module level where they are imported from db.db
    with patch('keyboards.menu.get_total_tickets_count', new_callable=AsyncMock) as mock_total, \
         patch('keyboards.menu.has_accepted_rules', new_callable=AsyncMock) as mock_rules, \
         patch('keyboards.menu.is_collection_closed', new_callable=AsyncMock) as mock_closed:

        mock_total.return_value = 1000
        mock_rules.return_value = True
        mock_closed.return_value = False

        kb, progress = await menu.get_main_menu_keyboard(228592391)
        print(f"DEBUG: Progress text is: \n{progress}")
        if "1000" in progress and "2500" in progress:
            print("✅ SUCCESS: Progress reflects 1000/2500 tickets.")
        else:
            print("❌ FAILURE: Progress does NOT reflect 1000/2500 tickets.")

    with patch('keyboards.menu.get_total_tickets_count', new_callable=AsyncMock) as mock_total, \
         patch('keyboards.menu.has_accepted_rules', new_callable=AsyncMock) as mock_rules, \
         patch('keyboards.menu.is_collection_closed', new_callable=AsyncMock) as mock_closed:

        mock_total.return_value = 500
        mock_rules.return_value = True
        mock_closed.return_value = False

        kb, progress = await menu.get_main_menu_keyboard(228592391)
        print(f"DEBUG: Progress text is: \n{progress}")
        if "741" in progress and "2500" in progress:
            print("✅ SUCCESS: Progress reflects fake floor 741/2500 tickets.")
        else:
            print("❌ FAILURE: Progress does NOT reflect fake floor 741/2500 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
