from db.db import (
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
            "Добро пожаловать в интеллектуальный квиз «iPhone 17»!\n\n"
            "Для участия тебе необходимо ознакомиться с правилами.\n\n"
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
        await message.answer(f"{progress}\n\nИспользуй меню для навигации.", reply_markup=kb, parse_mode="HTML")
        return

    kb, progress = await get_main_menu_keyboard(user_id)

    await message.answer(
        f"<b>Добро пожаловать в интеллектуальный квиз «iPhone 17»!</b>\n\n"
        "Участвуй в квизе, отвечай на вопросы и получай билеты на розыгрыш iPhone 17.\n\n"
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
        "<b>Спасибо! Теперь ты можешь участвовать в розыгрыше.</b>\n\n"
        "Нажимай «🎁 Играть», чтобы получить свои первые билеты!\n\n"
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
        "1. Стоимость участия — <b>99 ₽</b> за одну попытку.\n"
        "2. Каждая попытка даёт <b>1 гарантированный билет</b>.\n"
        "3. Дополнительно можно получить <b>до 3 бонусных билетов</b>, ответив правильно на вопросы квиза:\n"
        "   — 10 верных: +3 билета\n"
        "   — 9 верных: +2 билета\n"
        "   — 8 верных: +1 билет\n"
        "4. Сбор билетов завершается при достижении <b>2500 билетов</b> или <b>10 апреля 2026 года</b>.\n"
        "5. Победитель будет выбран случайным образом через random.org среди всех выданных номеров билетов.\n"
        "6. Розыгрыш пройдёт в прямом эфире в канале @mozgo_boy.\n\n"
        "Полные правила: <a href='https://cbda.ru/rules/base'>cbda.ru/rules/base</a>"
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Нажимай «🎁 Играть», чтобы участвовать!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        for t_num, status, score in apps:
            text += f"🎟 №{t_num:05d}\n"

        text += "\nВсе твои билеты участвуют в розыгрыше iPhone 17!"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard(limit=20)
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
    user_id = message.from_user.id
    kb, progress = await get_main_menu_keyboard(user_id)
    await message.answer(f"🔄 Данные обновлены!\n\n{progress}", reply_markup=kb, parse_mode="HTML")
