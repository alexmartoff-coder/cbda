from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import OWNER_ID
from db.db_admin import get_all_users_data
from db.db import DB_PATH, add_user
from keyboards.menu import get_admin_keyboard, get_db_download_keyboard, get_main_menu_keyboard
from utils.google_sheets import export_to_google_sheets
import os
import aiosqlite
import asyncio
import random
from datetime import datetime

router = Router()

@router.message(Command("admin"))
@router.message(F.text == "👨‍💼 Админ-панель")
async def cmd_admin(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    await message.answer("🛠 <b>Панель администратора</b>",
                         reply_markup=get_admin_keyboard(),
                         parse_mode="HTML")

@router.message(F.text == "📊 Экспорт в Google Sheets")
async def admin_export_google(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    status_msg = await message.answer("⏳ Подготовка данных и выгрузка в Google Sheets...")

    data = await get_all_users_data()
    url, error = await export_to_google_sheets(data)

    if error:
        await status_msg.edit_text(f"❌ Ошибка при экспорте:\n{error}")
    else:
        await status_msg.edit_text(f"✅ Данные успешно выгружены!\n\n🔗 <a href='{url}'>Открыть Google Таблицу</a>",
                                  parse_mode="HTML",
                                  disable_web_page_preview=False)

@router.message(Command("set_winner"))
async def cmd_set_winner(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /set_winner <номер_билета>")
        return

    try:
        ticket_number = int(args[1])
    except ValueError:
        await message.answer("Номер билета должен быть числом.")
        return

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM tickets WHERE ticket_number = ?", (ticket_number,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await message.answer(f"Билет №{ticket_number:05d} не найден.")
                return
            user_id = row[0]

        win_code = "".join([str(random.randint(0,9)) for _ in range(6)])
        await db.execute("INSERT OR REPLACE INTO winners (user_id, ticket_number, code) VALUES (?, ?, ?)",
                         (user_id, ticket_number, win_code))
        await db.commit()

        # Get winner info for notification
        async with db.execute("SELECT username, full_name FROM users WHERE user_id = ?", (user_id,)) as cursor:
            u = await cursor.fetchone()
            name = f"@{u[0]}" if (u and u[0]) else (u[1] if u else "Участник")

    await message.answer(
        f"🏆 Победитель установлен!\n\n"
        f"Билет №{ticket_number:05d}\n"
        f"Участник: {name}\n"
        f"Код: {win_code}"
    )

    # Notify winner
    win_msg = (
        "🎉 <b>ПОЗДРАВЛЯЕМ! ТЫ ВЫИГРАЛ IPHONE 17!</b>\n\n"
        "Твой билет №{:05d} стал выигрышным!\n\n".format(ticket_number) +
        f"🔑 Твой секретный код: <code>{win_code}</code>\n\n"
        "⚠️ <b>Что делать дальше:</b>\n"
        "1. Сохрани этот код и никому его не говори.\n"
        "2. Напиши организатору на почту alexandr@cbda.ru\n"
        "3. Укажи свой Telegram ID и секретный код для получения приза."
    )
    try:
        await message.bot.send_message(user_id, win_msg, parse_mode="HTML")
    except:
        await message.answer("Не удалось отправить сообщение победителю (возможно, бот заблокирован).")

@router.message(F.text == "🏆 Победитель")
async def admin_winner(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT w.user_id, w.ticket_number, w.code, w.won_at,
                   u.username, u.full_name
            FROM winners w
            JOIN users u ON w.user_id = u.user_id
            LIMIT 1
        """
        async with db.execute(query) as cursor:
            winner = await cursor.fetchone()

    if not winner:
        await message.answer("ℹ️ Победитель ещё не определён.\nДля установки используйте /set_winner <номер_билета>",
                             reply_markup=get_db_download_keyboard())
        return

    uid, t_num, code, won_at, username, full_name = winner

    name = f"@{username}" if username else full_name

    text = (
        f"🏆 <b>Информация о победителе</b>\n\n"
        f"Победитель: {name}\n"
        f"Заявка №{t_num:05d}\n"
        f"Секретный код: <code>{code}</code>\n"
        f"Дата выигрыша: {won_at}"
    )

    await message.answer(text, reply_markup=get_db_download_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "download_db")
async def download_db(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    if os.path.exists(DB_PATH):
        await callback.message.answer_document(FSInputFile(DB_PATH), caption="📂 Актуальная база данных (SQLite)")
    else:
        await callback.answer("Файл базы данных не найден", show_alert=True)

    await callback.answer()

@router.message(F.text == "🔙 Назад в главное меню")
async def back_to_main(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    kb, progress = await get_main_menu_keyboard(message.from_user.id)
    await message.answer(f"{progress}\n\nПереходим в главное меню...", reply_markup=kb, parse_mode="HTML")
