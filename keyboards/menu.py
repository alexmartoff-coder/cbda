import aiosqlite
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import is_collection_closed, has_user_used_free_attempt, get_total_tickets_count, get_paid_tickets_count
from database.db_final import is_final_registration_open, has_user_registered_for_final, get_user_finalist_tickets, is_final_active
from config import OWNER_ID, TICKET_LIMIT, INITIAL_FAKE_TICKETS
from utils.time_utils import get_moscow_now

async def get_main_menu_keyboard(user_id: int = None):
    from database.db import has_accepted_rules, get_user_ticket_counts
    rules_accepted = await has_accepted_rules(user_id) if user_id else False
    closed = await is_collection_closed()

    real_total = await get_total_tickets_count()

    # Логика прогресс-бара:
    # 1. Психологический пол 741 билета.
    # 2. Видимое кол-во = max(741, общее реальное кол-во билетов).
    display_count = max(INITIAL_FAKE_TICKETS, real_total)

    if display_count > TICKET_LIMIT:
        display_count = TICKET_LIMIT

    percent = int((display_count / TICKET_LIMIT) * 100)
    bar_length = 20
    filled_length = int(bar_length * display_count // TICKET_LIMIT)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    buttons = []

    if not closed:
        if rules_accepted:
            progress_text = f"📊 Сбор билетов: {display_count} из {TICKET_LIMIT}\n{bar} {percent}%"
        else:
            progress_text = "Примите правила конкурса, чтобы видеть прогресс и участвовать."

        buttons.append([KeyboardButton(text="🎁 Играть в Квиз за iPhone 17")])
        buttons.append([KeyboardButton(text="🏆 Лидерборд")])

    elif await is_final_active():
        from database.db_final import get_final_stats
        from datetime import datetime, timedelta
        stats = await get_final_stats()
        # times уже получен выше
        remaining = times["final_end"] - get_moscow_now().replace(tzinfo=None)
        rem_str = str(remaining).split(".")[0]

        # Личный прогресс
        finalist_tickets = await get_user_finalist_tickets(user_id)
        from database.db import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM final_results WHERE user_id = ? AND is_mini_quiz = 0", (user_id,)) as c:
                row = await c.fetchone()
                done_count = row[0] if row else 0

        progress_text = (
            f"🏆 ФИНАЛ В РАЗГАРЕ!\n"
            f"Всего финалистов (заявок): {stats['total_finalist_tickets']}\n"
            f"📈 Зарегистрировано: {stats['registered_tickets']} заявок\n"
            f"✅ Завершено: {stats['finished_tickets']}\n"
            f"🎟 Ваши квизы: {done_count}/{len(finalist_tickets)}\n"
            f"⏳ До 21:00 МСК: {rem_str}"
        )

        if await is_final_registration_open():
            tickets = await get_user_finalist_tickets(user_id)
            if tickets and not await has_user_registered_for_final(user_id):
                buttons.append([KeyboardButton(text="🏆 Войти в Финал")])
    else:
        # Проверка на мини-квиз
        from database.db_winner import get_user_mini_quiz_tickets, check_for_ties
        ties = await check_for_ties()
        # times уже получен выше
        now = get_moscow_now().replace(tzinfo=None)

        if ties and times:
            from datetime import timedelta
            mini_start = times["final_end"] + timedelta(minutes=30)
            if now < mini_start:
                remaining = mini_start - now
                rem_str = str(remaining).split(".")[0]
                progress_text = f"📢 Выявлено равенство результатов!\n⏳ Мини-квиз через: {rem_str}"
            else:
                progress_text = "🔥 МИНИ-КВИЗ ИДЁТ!"

            mini_tickets = await get_user_mini_quiz_tickets(user_id)
            if mini_tickets:
                buttons.append([KeyboardButton(text="🔥 Начать мини-квиз")])
        # Проверяем, не подведены ли итоги
        from database.db import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT value FROM settings WHERE key = 'results_published'") as c:
                published = await c.fetchone()
                if published and published[0] == '1':
                    from database.db_final import get_final_stats
                    stats = await get_final_stats()
                    y = stats['total_finalist_tickets']
                    x = stats['registered_tickets']
                    k = stats['finished_tickets']

                    progress_text = (
                        "🎉 ФИНАЛ ЗАВЕРШЁН!\n\n"
                        f"Всего финалистов (заявок): {y}\n"
                        f"📈 Зарегистрировано: {x}\n"
                        f"✅ Завершено: {k}\n"
                        "🏆 Победитель в канале @mozgo_boy"
                    )
                else:
                    progress_text = "🎉 Сбор билетов завершён досрочно!\n\nМы набрали 2500+ билетов. Спасибо всем участникам!\n\nРозыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy."

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
