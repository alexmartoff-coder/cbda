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

@router.message(F.text == "🏁 Управление Финалом")
async def admin_final_management(message: Message):
    if message.from_user.id != OWNER_ID: return

    from database.db import get_total_tickets_count
    total_tickets = await get_total_tickets_count()

    text = (
        f"🏁 <b>Управление конкурсом</b>\n\n"
        f"Всего выдано билетов: {total_tickets}\n"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Сид тестовых данных (2495)", callback_data="admin_seed_data")],
        [InlineKeyboardButton(text="🛠 Сид тестовых данных (741)", callback_data="admin_seed_data_741")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "admin_seed_data")
async def admin_seed_data_handler(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from tests.seed_test_data import seed_data
    await seed_data(2495)
    await callback.message.answer("✅ База данных засеяна (2495 билетов)!")
    await callback.answer()

@router.callback_query(F.data == "admin_seed_data_741")
async def admin_seed_data_741_handler(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from tests.seed_test_data import seed_data
    await seed_data(741)
    await callback.message.answer("✅ База данных засеяна (741 билет)!")
    await callback.answer()

@router.message(F.text == "🏆 Победитель")
async def admin_winner(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    await message.answer("ℹ️ Победитель будет выбран в прямом эфире с помощью random.org.\nДля выгрузки всех билетов используйте кнопку ниже.",
                         reply_markup=get_db_download_keyboard())

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
