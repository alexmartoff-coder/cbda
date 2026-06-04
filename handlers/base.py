from database.db import (
    add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure,
    has_user_used_free_attempt, get_user_applications, issue_ticket, set_quiz_session,
    has_accepted_rules, mark_rules_accepted
)
import aiosqlite
from keyboards.menu import get_main_menu_keyboard, get_start_quiz_keyboard, get_rules_agreement_keyboard
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)
    await check_and_trigger_closure(message.bot)

    if not await has_accepted_rules(user_id):
        agreement_text = (
            "Добро пожаловать в интеллектуальный квиз за iPhone 17!\n\n"
            "Для участия вам необходимо ознакомиться с правилами.\n\n"
            "«Я ознакомлен с <a href='https://cbda.ru/rules/base'>правилами конкурса</a> и согласен с их условиями, "
            "включая обработку моих данных (Telegram ID, username, результаты) в целях проведения конкурса. "
            "Данные не являются персональными по 152-ФЗ»."
        )
        kb, progress = await get_main_menu_keyboard(user_id)
        await message.answer(
            agreement_text,
            reply_markup=get_rules_agreement_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        await message.answer(f"{progress}\n\nИспользуйте меню для навигации.", reply_markup=kb, parse_mode="HTML")
        return

    kb, progress = await get_main_menu_keyboard(user_id)

    await message.answer(
        f"<b>Добро пожаловать в интеллектуальный квиз за iPhone 17!</b>\n\n"
        "Жми «🎁 Играть в Квиз за iPhone 17»!\n\n"
        f"{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "accept_rules")
async def accept_rules_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    await mark_rules_accepted(user_id)
    await callback.answer("✅ Правила приняты!")

    kb, progress = await get_main_menu_keyboard(user_id)
    await callback.message.answer(
        "<b>Спасибо! Теперь вы можете участвовать в конкурсе.</b>\n\n"
        "Жми «🎁 Играть в Квиз за iPhone 17»!\n\n"
        f"{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    try:
        await callback.message.delete()
    except:
        pass


@router.message(F.text == "🔥 Начать мини-квиз")
async def cmd_start_mini_quiz(message: Message):
    user_id = message.from_user.id
    from database.db_winner import get_user_mini_quiz_tickets
    tickets = await get_user_mini_quiz_tickets(user_id)
    if not tickets:
        await message.answer("У вас нет заявок для мини-квиза.")
        return

    await message.answer(
        f"🚀 Начинаем мини-квиз для {len(tickets)} заявок!\n\n"
        "⚠️ <b>Внимание!</b> Когда будете проходить квиз, выбирайте время и место, чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
        "При закрытии окна или выходе из приложения отсутствие ответов будет оцениваться как проигрыш.",
        parse_mode="HTML"
    )
    from handlers.final_quiz import start_final_quiz_for_ticket
    from utils.state_helper import get_state
    state = await get_state(message.bot, user_id)
    await start_final_quiz_for_ticket(message.bot, user_id, tickets[0], q_count=5, is_mini=True, state=state)

@router.message(F.text == "🏆 Войти в Финал")
async def cmd_enter_final(message: Message):
    user_id = message.from_user.id
    from database.db_final import is_final_registration_open, has_user_registered_for_final, get_user_finalist_tickets, register_for_final
    import aiosqlite

    if not await is_final_registration_open():
        await message.answer("Регистрация в Финал сейчас закрыта.")
        return

    if await has_user_registered_for_final(user_id):
        await message.answer("Вы уже вошли в Финал.")
        return

    tickets = await get_user_finalist_tickets(user_id)
    if not tickets:
        await message.answer("У вас нет финалистских заявок.")
        return

    await register_for_final(user_id)

    # Инициализация сессии финала
    from database.db import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO final_sessions (user_id, current_ticket_index, is_active) VALUES (?, 0, 1)", (user_id,))
        await db.commit()

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Начать финальный квиз", callback_data=f"start_next_final_{tickets[0]}")]
    ])

    await message.answer(
        f"✅ Вы успешно вошли в Финал!\n"
        f"Всего ваших заявок: {len(tickets)}\n\n"
        "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
        "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
        f"Нажмите на кнопку ниже, чтобы начать прохождение для заявки №{tickets[0]:05d}.",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.message(F.text == "📜 Правила розыгрыша")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📌 Правила розыгрыша iPhone 17</b>\n\n"
        "1. Дополнительные билеты можно получить за поддержку проекта (99 ₽).\n"
        "2. Каждый платёж (99 ₽) даёт:\n"
        "   — 1 гарантированный базовый билет\n"
        "   — До +3 бонусных билетов за результат в квизе:\n"
        "     • 10 верных ответов → +3 билета\n"
        "     • 9 верных ответов → +2 билета\n"
        "     • 8 верных ответов → +1 билет\n"
        "3. Сбор билетов останавливается при достижении 2500 билетов или 10 апреля 2026 года.\n"
        "4. Победитель будет выбран случайным образом через random.org среди всех выданных номеров билетов.\n\n"
        "Полные правила: <a href='https://cbda.ru/rules/base'>ссылка</a>\n\n"
        "Участие в конкурсе означает полное согласие с правилами."
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Жми «🎁 Играть в Квиз за iPhone 17»!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        for t_num, status, score in apps:
            if status == "pending":
                status_text = "⏳ Ожидает квиза"
                score_text = ""
            else:
                status_text = "✅ Участвует в розыгрыше"
                score_text = f" (результат {score}/10)" if score is not None else ""

            text += f"🎫 №{t_num:05d} {status_text}{score_text}\n"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
@router.message(F.text == "📊 Лидерборд финалистов")
async def cmd_leaderboard(message: Message):
    from database.db import DB_PATH
    # Проверка, завершен ли розыгрыш
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, ticket_number, code FROM winners LIMIT 1") as cursor:
            winner = await cursor.fetchone()

    if winner:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT username, full_name FROM users WHERE user_id = ?", (winner[0],)) as c:
                u = await c.fetchone()
                username = "@" + u[0] if (u and u[0]) else (u[1] if u else "Участник")

        text = (
            "🏆 <b>Розыгрыш завершён!</b>\n\n"
            f"Победитель: {username}\n"
            f"Выигрышный билет: №{winner[1]:05d}\n\n"
            "Приз: iPhone 17 PRO 256 Гб\n"
            "Следите за нашими новыми конкурсами!"
        )
        await message.answer(text, parse_mode="HTML")
        return

    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд финалистов пока пуст.")
        return

    text = "🏆 <b>Топ-20 участников по количеству финалистских заявок:</b>\n\n"
    for i, (username, full_name, finalist_count) in enumerate(leaders, 1):
        name = username if username else full_name
        text += f"{i}. {name} — <b>{finalist_count}</b> фин. заявок\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота по электронной почте alexandr@cbda.ru")

@router.message(F.text == "🔄 Обновить данные")
async def cmd_refresh(message: Message):
    from database.db import DB_PATH
    # Проверка, завершен ли розыгрыш
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, ticket_number FROM winners LIMIT 1") as cursor:
            winner = await cursor.fetchone()

    if winner:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT username, full_name FROM users WHERE user_id = ?", (winner[0],)) as c:
                u = await c.fetchone()
                username = "@" + u[0] if (u and u[0]) else (u[1] if u else "Участник")

        text = (
            "🏆 <b>Розыгрыш завершён!</b>\n\n"
            f"Победитель: {username}\n"
            f"Выигрышный билет: №{winner[1]:05d}\n\n"
            "Приз: iPhone 17 PRO 256 Гб\n\n"
            "Поздравляем победителя!\n"
            "<b>ЖДЁМ ВАС НА НОВЫХ КОНКУРСАХ!</b>\n"
            "Следите за стартом в нашем канале @mozgo_boy"
        )
        await message.answer(text, parse_mode="HTML")
        return

    user_id = message.from_user.id
    kb, progress = await get_main_menu_keyboard(user_id)
    await message.answer(f"🔄 Данные обновлены!\n\n{progress}", reply_markup=kb, parse_mode="HTML")
