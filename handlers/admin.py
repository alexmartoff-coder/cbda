from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from keyboards.menu import get_admin_keyboard, get_main_menu_keyboard
from config import OWNER_ID
import aiosqlite
from db.db import DB_PATH

router = Router()

@router.message(Command("admin"))
@router.message(F.text == "👨‍💼 Админ-панель")
async def cmd_admin(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer("Админ-панель", reply_markup=get_admin_keyboard())

@router.message(F.text == "🔙 Назад в главное menu")
@router.message(F.text == "🔙 Назад в главное меню")
async def cmd_back_to_main(message: Message):
    kb, progress = await get_main_menu_keyboard(message.from_user.id)
    await message.answer(f"Возвращаемся в меню.\n\n{progress}", reply_markup=kb, parse_mode="HTML")

@router.message(Command("set_winner"))
async def cmd_set_winner_direct(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /set_winner <номер_билета>")
        return

    try:
        t_num = int(parts[1])
    except:
        await message.answer("Некорректный номер билета")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM tickets WHERE ticket_number = ?", (t_num,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await message.answer(f"Билет №{t_num} не найден в базе")
                return
            uid = row[0]

        await db.execute("INSERT OR REPLACE INTO winners (user_id, ticket_number, code) VALUES (?, ?, ?)",
                         (uid, t_num, "SECRET123"))
        await db.commit()

    await message.answer(f"🏆 Победитель установлен: Билет №{t_num:05d}, User ID: {uid}")

@router.message(F.text == "🏆 Установить победителя")
async def cmd_set_winner_btn(message: Message):
    if message.from_user.id != OWNER_ID:
        return
    await message.answer("Для установки победителя используйте команду:\n/set_winner <номер_билета>")
