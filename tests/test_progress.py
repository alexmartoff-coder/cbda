import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from keyboards.menu import get_main_menu_keyboard

class AsyncContextManagerMock:
    def __init__(self, return_value):
        self.return_value = return_value
    async def __aenter__(self):
        return self.return_value
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    def __call__(self, *args, **kwargs):
        return self

async def test_progress():
    with patch('keyboards.menu.get_total_tickets_count') as mock_total:
        with patch('keyboards.menu.get_paid_tickets_count') as mock_paid:
            with patch('keyboards.menu.is_collection_closed') as mock_closed:
                with patch('database.db.has_accepted_rules') as mock_rules:
                    with patch('database.db_final.get_final_times') as mock_times:
                        with patch('database.db_final.is_final_active') as mock_final_active:
                            mock_total.return_value = 800
                            mock_paid.return_value = 500
                            mock_closed.return_value = False
                            mock_rules.return_value = True
                            mock_times.return_value = None
                            mock_final_active.return_value = False

                            with patch('aiosqlite.connect') as mock_connect:
                                mock_cursor = AsyncMock()
                                mock_cursor.fetchone.return_value = (0,)

                                mock_db = AsyncMock()
                                # db.execute(...) is called and returns an ACM
                                mock_db.execute = MagicMock(return_value=AsyncContextManagerMock(mock_cursor))

                                # aiosqlite.connect(...) is called and returns an ACM
                                mock_connect.return_value = AsyncContextManagerMock(mock_db)

                                kb, progress = await get_main_menu_keyboard(228592391)
                                print(f"DEBUG: Progress text is: \n{progress}")
                                if "800" in progress:
                                    print("✅ SUCCESS: Progress reflects 800 tickets.")
                                else:
                                    print("❌ FAILURE: Progress does NOT reflect 800 tickets.")

if __name__ == "__main__":
    asyncio.run(test_progress())
