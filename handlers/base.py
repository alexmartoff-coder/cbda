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
            "Добро пожаловать в интеллектуальный квиз с розыгрышем iPhone 17!\n\n"
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
        f"<b>Добро пожаловать в интеллектуальный квиз с розыгрышем iPhone 17!</b>\n\n"
        "Участвуйте, отвечайте на вопросы и выигрывайте призы!\n\n"
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
        "<b>Спасибо! Теперь вы можете участвовать в квизе.</b>\n\n"
        "Участвуйте, отвечайте на вопросы и выигрывайте призы!\n\n"
        f"{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    try:
        await callback.message.delete()
    except:
        pass



@router.message(F.text == "📜 Правила розыгрыша")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📌 Правила розыгрыша iPhone 17</b>\n\n"
        "1. Стоимость участия — 99 ₽.\n"
        "2. Каждый платёж даёт 1 гарантированный базовый билет.\n"
        "3. После оплаты вы можете пройти квиз (10 вопросов).\n"
        "4. Бонусные билеты за результат в квизе:\n"
        "   — 10 правильных: +3 бонусных билета\n"
        "   — 9 правильных: +2 бонусных билета\n"
        "   — 8 правильных: +1 бонусный билет\n"
        "5. Сбор билетов останавливается при достижении 2500 билетов или 10 апреля 2026.\n"
        "6. Розыгрыш приза (iPhone 17) проводится честно в прямом эфире с помощью random.org среди всех выданных билетов.\n\n"
        "Полные правила: https://cbda.ru/rules/base\n"
        "Организатор: Частное лицо ИНН 470102947100."
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть», чтобы участвовать!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        for t_num, status, score in apps:
            text += f"🎫 №{t_num:05d}\n"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
async def cmd_leaderboard(message: Message):
    # В новой версии лидерборд - это топ по общему количеству билетов
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT u.username, u.full_name, COUNT(t.id) as ticket_count
            FROM users u
            JOIN tickets t ON u.user_id = t.user_id
            GROUP BY u.user_id
            ORDER BY ticket_count DESC
            LIMIT 20
        """) as cursor:
            leaders = await cursor.fetchall()

    if not leaders:
        await message.answer("Лидерборд пока пуст.")
        return

    text = "🏆 <b>Топ-20 участников по количеству билетов:</b>\n\n"
    for i, (username, full_name, ticket_count) in enumerate(leaders, 1):
        name = username if username else full_name
        text += f"{i}. {name} — <b>{ticket_count}</b> билетов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📞 Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота по электронной почте alexandr@cbda.ru")

@router.message(F.text == "🔄 Обновить данные")
async def cmd_refresh(message: Message):
    from database.db import DB_PATH
    # Проверка, завершен ли розыгрыш
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = 'results_published'") as cursor:
            published = await cursor.fetchone()

    if published:
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT user_id, ticket_number FROM winners LIMIT 1") as cursor:
                winner = await cursor.fetchone()

        if winner:
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT username, full_name FROM users WHERE user_id = ?", (winner[0],)) as c:
                    u = await c.fetchone()
                    username = "@" + u[0] if (u and u[0]) else (u[1] if u else "Участник")

            text = (
                "🏆 <b>Победитель конкурса определён!</b>\n\n"
                f"Победитель: {username} (билет №{winner[1]:05d})\n"
                "Приз: iPhone 17\n\n"
                "Поздравляем победителя!\n"
                "<b>ЖДЁМ ВАС НА НОВЫХ КОНКУРСАХ!</b>\n"
                "Следите за стартом в нашем канале @mozgo_boy"
            )
            await message.answer(text, parse_mode="HTML")
            return

    user_id = message.from_user.id
    kb, progress = await get_main_menu_keyboard(user_id)
    await message.answer(f"🔄 Данные обновлены!\n\n{progress}", reply_markup=kb, parse_mode="HTML")
