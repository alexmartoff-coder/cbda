import aiosqlite
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from db.db import is_collection_closed, get_total_tickets_count
from config import OWNER_ID, TICKET_LIMIT, INITIAL_FAKE_TICKETS

async def get_main_menu_keyboard(user_id: int = None):
    closed = await is_collection_closed()

    total_tickets = await get_total_tickets_count()
    visible_tickets = max(INITIAL_FAKE_TICKETS, total_tickets)
    if visible_tickets > TICKET_LIMIT:
        visible_tickets = TICKET_LIMIT

    percent = int((visible_tickets / TICKET_LIMIT) * 100)
    bar_length = 20
    filled_length = int(bar_length * visible_tickets // TICKET_LIMIT)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    progress_text = f"📊 Билетов собрано: <b>{visible_tickets}</b> из <b>{TICKET_LIMIT}</b>\n{bar} <b>{percent}%</b>"

    buttons = []

    if not closed:
        buttons.append([KeyboardButton(text="🎁 Играть в Квиз за iPhone 17")])

    # Проверяем наличие билетов, ожидающих квиза
    if user_id and not closed:
        from db.db import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND status = 'pending'", (user_id,)) as c:
                row = await c.fetchone()
                pending_count = row[0] if row else 0

        if pending_count > 0:
            buttons.append([KeyboardButton(text=f"🚀 Пройти квиз ({pending_count} в очереди)")])

    buttons.extend([
        [KeyboardButton(text="📜 Правила розыгрыша"), KeyboardButton(text="🎟️ Мои билеты")],
        [KeyboardButton(text="🏆 Лидерборд"), KeyboardButton(text="❓ Поддержка")]
    ])

    if user_id == OWNER_ID:
        buttons.append([KeyboardButton(text="👨‍💼 Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True), progress_text

def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="📊 Экспорт в Google Sheets")],
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
