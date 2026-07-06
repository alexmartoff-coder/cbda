import aiosqlite
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from db.db import is_collection_closed, get_total_tickets_count
from config import OWNER_ID, TICKET_LIMIT, INITIAL_FAKE_TICKETS
from utils.time_utils import get_moscow_now

async def get_main_menu_keyboard(user_id: int = None):
    from db.db import has_accepted_rules, get_user_ticket_counts
    rules_accepted = await has_accepted_rules(user_id) if user_id else False
    closed = await is_collection_closed()

    real_total = await get_total_tickets_count()

    # Логика прогресс-бара:
    # 1. Базовое смещение 741.
    # 2. Любой юзер всегда видит (Минимум 741) или реальный итог.

    display_count = max(INITIAL_FAKE_TICKETS, real_total)

    if display_count > TICKET_LIMIT:
        display_count = TICKET_LIMIT

    percent = int((display_count / TICKET_LIMIT) * 100)
    bar_length = 20
    filled_length = int(bar_length * display_count // TICKET_LIMIT)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    progress_text = f"📊 До розыгрыша: <b>{display_count}</b> из <b>{TICKET_LIMIT}</b> билетов\n{bar} <b>{percent}%</b>"

    buttons = []

    if rules_accepted and not closed:
        buttons.append([KeyboardButton(text="🎁 Играть в Квиз за iPhone 17")])

    # Если есть билеты в очереди на квиз, показываем кнопку
    if user_id:
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
        [KeyboardButton(text="🏆 Информация о победителе")],
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

def get_pay_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])
