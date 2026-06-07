import aiosqlite
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import is_collection_closed, get_total_tickets_count, get_user_ticket_counts
from config import OWNER_ID, TICKET_LIMIT, INITIAL_FAKE_TICKETS
from utils.time_utils import get_moscow_now

async def get_main_menu_keyboard(user_id: int = None):
    closed = await is_collection_closed()

    real_total = await get_total_tickets_count()
    user_total, _ = await get_user_ticket_counts(user_id) if user_id else (0, 0)

    # Логика прогресс-бара:
    # Психологический пол 741.
    # Видимые билеты = max(INITIAL_FAKE_TICKETS, real_total)
    display_count = max(INITIAL_FAKE_TICKETS, real_total)

    if display_count > TICKET_LIMIT:
        display_count = TICKET_LIMIT

    percent = int((display_count / TICKET_LIMIT) * 100)
    bar_length = 20
    filled_length = int(bar_length * display_count // TICKET_LIMIT)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    progress_text = f"📊 До розыгрыша осталось: {display_count} из {TICKET_LIMIT} билетов\n{bar} {percent}%"

    buttons = []

    if not closed:
        buttons.append([KeyboardButton(text="🎁 Играть в Квиз за iPhone 17")])

        # Проверяем наличие билетов, ожидающих квиза
        if user_id:
            from database.db import DB_PATH
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND status = 'issued'", (user_id,)) as c:
                    row = await c.fetchone()
                    pending_count = row[0] if row else 0

            if pending_count > 0:
                buttons.append([KeyboardButton(text=f"🚀 Пройти квиз ({pending_count} в очереди)")])

    buttons.append([KeyboardButton(text="🏆 Лидерборд")])
    buttons.extend([
        [KeyboardButton(text="🎟️ Мои билеты"), KeyboardButton(text="📜 Правила розыгрыша")],
        [KeyboardButton(text="❓ Поддержка"), KeyboardButton(text="🔄 Обновить данные")]
    ])

    if user_id == OWNER_ID:
        buttons.append([KeyboardButton(text="👨‍💼 Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True), progress_text

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
