from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import OWNER_ID
from db.db import DB_PATH, issue_ticket, get_total_tickets_count
from keyboards.menu import get_admin_keyboard, get_db_download_keyboard, get_main_menu_keyboard
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
    await message.answer("Экспорт временно недоступен. Используйте выгрузку SQLite.")

@router.message(F.text == "🏆 Победитель")
async def admin_winner(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, ticket_number, code, won_at FROM winners LIMIT 1") as cursor:
            winner = await cursor.fetchone()

    if not winner:
        await message.answer("ℹ️ Победитель ещё не определён.",
                             reply_markup=get_db_download_keyboard())
        return

    uid, t_num, code, won_at = winner
    text = (
        f"🏆 <b>Информация о победителе</b>\n\n"
        f"Заявка №{t_num:05d}\n"
        f"Секретный код: <code>{code}</code>\n"
        f"Дата генерации: {won_at}"
    )
    await message.answer(text, reply_markup=get_db_download_keyboard(), parse_mode="HTML")

@router.message(Command("set_winner"))
async def cmd_set_winner(message: Message):
    if message.from_user.id != OWNER_ID: return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /set_winner <ticket_number>")
        return

    try:
        t_num = int(parts[1])
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id FROM tickets WHERE ticket_number = ?", (t_num,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    await message.answer("Билет не найден в базе.")
                    return
                user_id = row[0]

            import random
            code = "".join([str(random.randint(0,9)) for _ in range(6)])
            await db.execute("INSERT OR REPLACE INTO winners (user_id, ticket_number, code) VALUES (?, ?, ?)",
                             (user_id, t_num, code))
            await db.commit()

        await message.answer(f"✅ Победитель установлен! Билет №{t_num:05d}, код: {code}")

        win_msg = (
            "🎉 <b>Поздравляем! Ваш билет выиграл iPhone 17!</b>\n\n"
            f"🔑 Ваш секретный код: <code>{code}</code>\n\n"
            "Для получения приза напишите нам: alexandr@cbda.ru"
        )
        try: await message.bot.send_message(user_id, win_msg, parse_mode="HTML")
        except: pass

    except Exception as e:
        await message.answer(f"Ошибка: {e}")

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
