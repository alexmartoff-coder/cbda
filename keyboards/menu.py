import aiosqlite
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from db.db import is_collection_closed, get_total_tickets_count
from config import OWNER_ID, TICKET_LIMIT, INITIAL_FAKE_TICKETS

async def get_main_menu_keyboard(user_id: int = None):
    closed = await is_collection_closed()
    total_real = await get_total_tickets_count()
    display_count = min(max(INITIAL_FAKE_TICKETS, total_real), TICKET_LIMIT)

    percent = int((display_count / TICKET_LIMIT) * 100)
    bar_length = 20
    filled_length = int(bar_length * display_count // TICKET_LIMIT)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    if closed:
        progress_text = "🎉 <b>Сбор билетов завершён досрочно!</b>\n\nМы набрали 2500+ билетов. Спасибо всем участникам!"
        buttons = [
            [KeyboardButton(text="📜 Правила розыгрыша")],
            [KeyboardButton(text="🎟️ Мои билеты"), KeyboardButton(text="🏆 Лидерборд")],
            [KeyboardButton(text="❓ Поддержка")]
        ]
    else:
        progress_text = f"📊 Собрано билетов: <b>{display_count}</b> из <b>{TICKET_LIMIT}</b>\n{bar} <b>{percent}%</b>"
        buttons = [
            [KeyboardButton(text="🎁 Играть в Квиз за iPhone 17")],
            [KeyboardButton(text="📜 Правила розыгрыша")],
            [KeyboardButton(text="🎟️ Мои билеты"), KeyboardButton(text="🏆 Лидерборд")],
            [KeyboardButton(text="❓ Поддержка")]
        ]

    if user_id == OWNER_ID:
        buttons.append([KeyboardButton(text="👨‍💼 Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True), progress_text

def get_closed_generic_keyboard():
    buttons = [
        [KeyboardButton(text="📜 Правила розыгрыша")],
        [KeyboardButton(text="🎟️ Мои билеты"), KeyboardButton(text="🏆 Лидерборд")],
        [KeyboardButton(text="❓ Поддержка")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="📊 Экспорт в Google Sheets")],
        [KeyboardButton(text="🏁 Управление Финалом")],
        [KeyboardButton(text="🏆 Победитель")],
        [KeyboardButton(text="🔙 Назад в главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_db_download_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать базу данных (SQLITE)", callback_data="download_db")]
    ])

def get_start_quiz_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать квиз", callback_data="start_quiz")]
    ])

def get_rules_agreement_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я ознакомлен и согласен", callback_data="accept_rules")]
    ])
