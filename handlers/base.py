import aiosqlite
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from db.db import (
    add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure,
    get_user_applications, has_accepted_rules, mark_rules_accepted, DB_PATH
)
from keyboards.menu import get_main_menu_keyboard, get_rules_agreement_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)
    await check_and_trigger_closure(message.bot)

    # A mandatory rules acceptance flow is implemented; users cannot participate or see the progress bar until they accept terms.
    if not await has_accepted_rules(user_id):
        agreement_text = (
            "Добро пожаловать в интеллектуальный конкурс «iPhone 17 PRO 256 Гб»!\n\n"
            "Для участия вам необходимо ознакомиться с правилами.\n\n"
            "«Я ознакомлен с <a href='https://cbda.ru/rules/base'>правилами конкурса</a> и согласен с их условиями, "
            "включая обработку моих данных (Telegram ID, username, результаты) в целях проведения конкурса. "
            "Данные не являются персональными по 152-ФЗ»."
        )
        await message.answer(
            agreement_text,
            reply_markup=get_rules_agreement_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        return

    kb, progress = await get_main_menu_keyboard(user_id)
    await message.answer(
        f"<b>Добро пожаловать в интеллектуальный конкурс «iPhone 17 PRO 256 Гб»!</b>\n\n"
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
        "<b>📜 Правила розыгрыша «iPhone 17»</b>\n\n"
        "• <b>Стоимость участия:</b> 99 ₽.\n"
        "• Каждый платёж гарантирует получение <b>1 базового билета</b>.\n"
        "• За прохождение квиза (10 вопросов) можно получить дополнительные бонусные билеты:\n"
        "  - 10 правильных ответов: <b>+3 бонусных билета</b>\n"
        "  - 9 правильных ответов: <b>+2 бонусных билета</b>\n"
        "  - 8 правильных ответов: <b>+1 бонусный билет</b>\n"
        "• <b>Сбор билетов:</b> останавливается при достижении 2500 билетов или 10 апреля 2026 г.\n"
        "• <b>Розыгрыш:</b> проводится честно среди всех выданных билетов в прямом эфире в канале @mozgo_boy.\n"
        "• Победитель будет выбран случайным образом с помощью сайта <a href='https://www.random.org/'>random.org</a>.\n\n"
        "Ознакомиться с <a href='https://cbda.ru/rules/base'>полной версией правил</a>.\n"
        "Участие в конкурсе означает полное согласие с правилами."
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    # The '🎟️ Мои билеты' command displays a list of user tickets with numbers (№XXXXX) that are eligible for the draw.
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Приобретай билеты в меню!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        for t_num, status, score in apps:
            if status == "pending":
                status_str = "⏳ Квиз не пройден"
            else:
                status_str = f"Оценка: {score}/10"
            text += f"🎫 №{t_num:05d} ({status_str})\n"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд пока пуст.")
        return

    text = "🏆 <b>Топ-20 участников по количеству билетов:</b>\n\n"
    for i, (username, full_name, tickets_count) in enumerate(leaders, 1):
        name = f"@{username}" if username else (full_name if full_name else "Участник")
        text += f"{i}. {name} — <b>{tickets_count}</b> билетов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку по адресу: alexandr@cbda.ru")
