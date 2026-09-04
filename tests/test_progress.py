import asyncio
from keyboards.menu import get_main_menu_keyboard

async def test_progress():
    kb, progress = await get_main_menu_keyboard(228592391)
    print(f"DEBUG: Progress text is:\n{progress}")

if __name__ == "__main__":
    asyncio.run(test_progress())
