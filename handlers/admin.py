from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from config import OWNER_ID
from db.db_admin import get_all_users_data
from db.db import DB_PATH
from keyboards.menu import get_admin_keyboard, get_db_download_keyboard, get_main_menu_keyboard
from utils.google_sheets import export_to_google_sheets
import os
import aiosqlite

router = Router()

@router.message(Command("admin"))
@router.message(F.text == "👨‍💼 Админ-панель")
async def cmd_admin(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    await message.answer(
        "🛠 <b>Панель администратора</b>",
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )

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
        await status_msg.edit_text(
            f"✅ Данные успешно выгружены!\n\n🔗 <a href='{url}'>Открыть Google Таблицу</a>",
            parse_mode="HTML",
            disable_web_page_preview=False
        )

@router.message(F.text == "🏆 Информация о победителе")
async def admin_winner(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    text = (
        "🏆 <b>Информация о победителе</b>\n\n"
        "Победитель выбирается в прямом эфире в канале @mozgo_boy с помощью сервиса https://www.random.org/\n"
        "среди всех выданных билетов."
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
