import aiosqlite
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import is_collection_closed, get_total_tickets_count, DB_PATH
from config import OWNER_ID, TICKET_LIMIT, INITIAL_FAKE_TICKETS

async def get_main_menu_keyboard(user_id: int = None):
    from database.db import has_accepted_rules
    rules_accepted = await has_accepted_rules(user_id) if user_id else False
    closed = await is_collection_closed()

    total_real_tickets = await get_total_tickets_count()

    # Логика прогресс-бара:
    # Visible tickets = max(INITIAL_FAKE_TICKETS, total_real_tickets)
    display_count = max(INITIAL_FAKE_TICKETS, total_real_tickets)

    if display_count > TICKET_LIMIT:
        display_count = TICKET_LIMIT

    percent = int((display_count / TICKET_LIMIT) * 100)
    bar_length = 20
    filled_length = int(bar_length * display_count // TICKET_LIMIT)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    buttons = []

    if not closed:
        progress_text = f"📊 До завершения сбора: {display_count} из {TICKET_LIMIT} билетов\n{bar} {percent}%"
        buttons.append([KeyboardButton(text="🎁 Играть в Квиз за iPhone 17")])
    else:
        progress_text = (
            "🎉 Сбор билетов завершён!\n\n"
            f"Всего билетов: {total_real_tickets}\n"
            "Розыгрыш в канале @mozgo_boy"
        )

    # Проверяем наличие билетов, ожидающих квиза
    if not closed and user_id:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND status = 'pending'", (user_id,)) as c:
                row = await c.fetchone()
                pending_count = row[0] if row else 0

        if pending_count > 0:
            buttons.append([KeyboardButton(text="🚀 Пройти квиз")])

    buttons.append([KeyboardButton(text="📜 Правила розыгрыша")])
    buttons.extend([
        [KeyboardButton(text="🎟️ Мои билеты"), KeyboardButton(text="🏆 Лидерборд")],
        [KeyboardButton(text="❓ Поддержка")]
    ])

    if user_id == OWNER_ID:
        buttons.append([KeyboardButton(text="👨‍💼 Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True), progress_text

def get_admin_keyboard():
    buttons = [
        [KeyboardButton(text="📊 Экспорт в Google Sheets")],
        [KeyboardButton(text="🏁 Управление Финалом")], # Keeping for compatibility if needed
        [KeyboardButton(text="🏆 Победитель")],
        [KeyboardButton(text="🔙 Назад в главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

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
