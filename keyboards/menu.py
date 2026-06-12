import aiosqlite
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import is_collection_closed, get_total_tickets_count
from config import OWNER_ID, TICKET_LIMIT, INITIAL_FAKE_TICKETS

async def get_main_menu_keyboard(user_id: int = None):
    from database.db import get_user_ticket_counts
    closed = await is_collection_closed()

    user_total, _ = await get_user_ticket_counts(user_id) if user_id else (0, 0)

    total_real_tickets = await get_total_tickets_count()
    display_count = max(INITIAL_FAKE_TICKETS + user_total, total_real_tickets)

    if display_count > TICKET_LIMIT:
        display_count = TICKET_LIMIT

    percent = int((display_count / TICKET_LIMIT) * 100)
    bar_length = 20
    filled_length = int(bar_length * display_count // TICKET_LIMIT)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    buttons = []

    if not closed:
        progress_text = f"📊 Прогресс сбора билетов: {display_count} из {TICKET_LIMIT}\n{bar} {percent}%"
        buttons.append([KeyboardButton(text="🎁 Играть в Квиз за iPhone 17")])

        # Проверяем наличие билетов, ожидающих квиза
        if user_id:
            from database.db import DB_PATH
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT COUNT(*) FROM tickets WHERE user_id = ? AND status = 'issued'", (user_id,)) as c:
                    row = await c.fetchone()
                    pending_count = row[0] if row else 0

            if pending_count > 0:
                buttons.append([KeyboardButton(text="🚀 Пройти квиз")])
    else:
        progress_text = (
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )

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
