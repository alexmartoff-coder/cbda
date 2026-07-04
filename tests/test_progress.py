import asyncio
from keyboards.menu import get_main_menu_keyboard
from unittest.mock import patch, MagicMock

async def test_progress():
    # Test case 1: 0 real tickets -> should show 741 (INITIAL_FAKE_TICKETS)
    with patch('keyboards.menu.get_total_tickets_count', new_callable=MagicMock) as mock_count:
        mock_count.return_value = asyncio.Future()
        mock_count.return_value.set_result(0)
        with patch('db.db.has_accepted_rules', new_callable=MagicMock) as mock_rules:
            mock_rules.return_value = asyncio.Future()
            mock_rules.return_value.set_result(True)
            with patch('keyboards.menu.is_collection_closed', new_callable=MagicMock) as mock_closed:
                mock_closed.return_value = asyncio.Future()
                mock_closed.return_value.set_result(False)

                kb, progress = await get_main_menu_keyboard(228592391)
                print(f"DEBUG 1: Progress text is: \n{progress}")
                if "741" in progress and "2500" in progress:
                    print("✅ SUCCESS 1: Progress reflects 741 tickets.")
                else:
                    print("❌ FAILURE 1: Progress does NOT reflect 741 tickets.")

    # Test case 2: 1000 real tickets -> should show 1000
    with patch('keyboards.menu.get_total_tickets_count', new_callable=MagicMock) as mock_count:
        mock_count.return_value = asyncio.Future()
        mock_count.return_value.set_result(1000)
        with patch('db.db.has_accepted_rules', new_callable=MagicMock) as mock_rules:
            mock_rules.return_value = asyncio.Future()
            mock_rules.return_value.set_result(True)
            with patch('keyboards.menu.is_collection_closed', new_callable=MagicMock) as mock_closed:
                mock_closed.return_value = asyncio.Future()
                mock_closed.return_value.set_result(False)

                kb, progress = await get_main_menu_keyboard(228592391)
                print(f"DEBUG 2: Progress text is: \n{progress}")
                if "1000" in progress and "2500" in progress:
                    print("✅ SUCCESS 2: Progress reflects 1000 tickets.")
                else:
                    print("❌ FAILURE 2: Progress does NOT reflect 1000 tickets.")

    # Test case 3: 3000 real tickets -> should show 2500 (TICKET_LIMIT)
    with patch('keyboards.menu.get_total_tickets_count', new_callable=MagicMock) as mock_count:
        mock_count.return_value = asyncio.Future()
        mock_count.return_value.set_result(3000)
        with patch('db.db.has_accepted_rules', new_callable=MagicMock) as mock_rules:
            mock_rules.return_value = asyncio.Future()
            mock_rules.return_value.set_result(True)
            with patch('keyboards.menu.is_collection_closed', new_callable=MagicMock) as mock_closed:
                mock_closed.return_value = asyncio.Future()
                mock_closed.return_value.set_result(False)

                kb, progress = await get_main_menu_keyboard(228592391)
                print(f"DEBUG 3: Progress text is: \n{progress}")
                if "2500" in progress:
                    print("✅ SUCCESS 3: Progress reflects 2500 tickets.")
                else:
                    print("❌ FAILURE 3: Progress does NOT reflect 2500 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
