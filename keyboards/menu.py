import aiosqlite
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from db.db import is_collection_closed, get_total_tickets_count, has_accepted_rules
from config import TICKET_LIMIT, INITIAL_FAKE_TICKETS, OWNER_ID

async def get_main_menu_keyboard(user_id: int = None):
    closed = await is_collection_closed()
    total_real = await get_total_tickets_count()

    # Progress bar logic
    # Maintain 741 psychological floor
    display_count = max(INITIAL_FAKE_TICKETS, total_real)
    if display_count > TICKET_LIMIT:
        display_count = TICKET_LIMIT

    percent = int((display_count / TICKET_LIMIT) * 100)
    bar_length = 20
    filled_length = int(bar_length * display_count // TICKET_LIMIT)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    # HTML bold tags (<b>) are used in the main menu progress bar for ticket counts and percentages
    progress_text = f"📊 До розыгрыша осталось: <b>{display_count}</b> из <b>{TICKET_LIMIT}</b> билетов\n{bar} <b>{percent}%</b>"

    buttons = []
    if not closed:
        buttons.append([KeyboardButton(text="🎁 Играть в Квиз за iPhone 17")])

    buttons.append([KeyboardButton(text="📜 Правила розыгрыша"), KeyboardButton(text="🎟️ Мои билеты")])
    buttons.append([KeyboardButton(text="🏆 Лидерборд"), KeyboardButton(text="❓ Поддержка")])

    if user_id == OWNER_ID:
        buttons.append([KeyboardButton(text="👨‍💼 Админ-панель")])

    kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return kb, progress_text

def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="📊 Экспорт в Google Sheets")],
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
