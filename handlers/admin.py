from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import OWNER_ID
from database.db_admin import get_all_users_data
from database.db import DB_PATH
from keyboards.menu import get_admin_keyboard, get_db_download_keyboard, get_main_menu_keyboard
from utils.google_sheets import export_to_google_sheets
import os
import aiosqlite
import asyncio
import random
from datetime import datetime, timedelta

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
        await message.answer("ℹ️ Победитель ещё не определён.\nДля полной выгрузки используйте кнопку ниже.",
                             reply_markup=get_db_download_keyboard())
        return

    uid, t_num, code, won_at, username, full_name = winner

    name = f"@{username}" if username else full_name

    try:
        dt = datetime.fromisoformat(won_at.replace(" ", "T"))
        date_str = dt.strftime("%d.%m.%Y %H:%M")
    except:
        date_str = won_at

    text = (
        f"🏆 <b>Информация о победителе</b>\n\n"
        f"Победитель: {name}\n"
        f"Заявка №{t_num:05d}\n"
        f"Секретный код: <code>{code}</code>\n"
        f"Дата генерации: {date_str}"
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
    await message.answer(f"{progress}\n\nПереходим в главное меню...", reply_markup=kb)
