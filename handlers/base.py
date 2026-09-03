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
            "Добро пожаловать в платный развлекательный квиз за 99 ₽ с розыгрышем iPhone 17!\n\n"
            "Для участия вам необходимо ознакомиться с правилами.\n\n"
            "«Я ознакомлен с <a href='https://cbda.ru/rules/base'>правилами розыгрыша</a> и согласен с их условиями, "
            "включая обработку моих данных (Telegram ID, username, результаты).»"
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
        f"<b>Добро пожаловать в платный развлекательный квиз с розыгрышем iPhone 17!</b>\n\n"
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
        "<b>Спасибо! Теперь вы можете участвовать в розыгрыше.</b>\n\n"
        f"{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    try:
        await callback.message.delete()
    except:
        pass

@router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def cmd_play_quiz(message: Message):
    user_id = message.from_user.id

    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    pay_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])

    mechanic_text = (
        "<b>📱 Квиз за iPhone 17</b>\n\n"
        "<b>Правила участия:</b>\n"
        "• Стоимость 1 попытки — 99 ₽\n"
        "• Каждый платёж гарантирует <b>1 базовый билет</b>\n"
        "• Ответь на 10 вопросов квиза и получи до <b>+3 бонусных билетов</b>:\n"
        "  - 10 правильных ответов → <b>+3 бонусных билета</b>\n"
        "  - 9 правильных ответов → <b>+2 бонусных билета</b>\n"
        "  - 8 правильных ответов → <b>+1 бонусный билет</b>\n"
        "  - меньше 8 → бонусных билетов нет\n\n"
        "Сбор билетов завершится при достижении 2500 билетов или 10 апреля 2026 года.\n"
        "Розыгрыш пройдет честно среди всех участников в прямом эфире в канале @mozgo_boy с помощью https://www.random.org/\n\n"
        "Готов испытать удачу?"
    )

    await message.answer(mechanic_text, reply_markup=pay_kb, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "📜 Правила розыгрыша")
@router.message(F.text == "❓ Правила конкурса")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📜 Правила розыгрыша iPhone 17</b>\n\n"
        "• Каждый платёж 99 ₽ даёт 1 гарантированный базовый билет.\n"
        "• Прохождение квиза из 10 вопросов позволяет получить дополнительно до +3 бонусных билетов:\n"
        "  - 10/10 → +3 билета\n"
        "  - 9/10 → +2 билета\n"
        "  - 8/10 → +1 билет\n"
        "  - менее 8 → 0 бонусных билетов.\n"
        "• Сбор билетов останавливается при достижении 2500 билетов или 10 апреля 2026 года.\n"
        "• Розыгрыш проводится честно с помощью рандомайзера https://www.random.org/ в прямом эфире в канале @mozgo_boy.\n\n"
        "Все полученные билеты участвуют в итоговом розыгрыше!"
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
@router.message(F.text == "👤 Мои заявки")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть в Квиз за iPhone 17», чтобы получить билет!")
    else:
        text = "<b>🎟️ Твои билеты:</b>\n\n"
        for t_num, status, score in apps:
            if status == "pending":
                status_text = "⏳ Ожидает квиза"
            elif status == "completed":
                status_text = "✅ Активен"
            else:
                status_text = f"✅ Активен (Результат: {score}/10)"

            text += f"🎟️ №{t_num:05d} {status_text}\n"
        text += "\nВсе твои билеты участвуют в розыгрыше iPhone 17!"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
@router.message(F.text == "📊 Лидерборд")
@router.message(F.text == "📊 Лидерборд финалистов")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд пока пуст. Будь первым!")
        return

    text = "🏆 <b>Топ-20 участников по количеству билетов:</b>\n\n"
    for i, (username, full_name, ticket_count) in enumerate(leaders, 1):
        name = f"@{username}" if username else full_name
        text += f"{i}. {name} — <b>{ticket_count}</b> билетов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
@router.message(F.text == "📞 Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота: @mozgo_boy")
