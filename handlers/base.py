from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from db.db import (
    add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure,
    get_user_applications, has_accepted_rules, mark_rules_accepted
)
from keyboards.menu import get_main_menu_keyboard, get_rules_agreement_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)
    await check_and_trigger_closure(message.bot)

    if not await has_accepted_rules(user_id):
        agreement_text = (
            "Добро пожаловать в викторину «iPhone 17»!\n\n"
            "Для участия вам необходимо ознакомиться с правилами.\n\n"
            "«Я ознакомлен с <a href='https://cbda.ru/rules/base'>правилами конкурса</a> и согласен с их условиями, "
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
        f"<b>Добро пожаловать в викторину «iPhone 17»!</b>\n\n"
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
        f"{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    try:
        await callback.message.delete()
    except Exception:
        pass

@router.message(F.text == "📜 Правила розыгрыша")
@router.message(F.text == "❓ Правила конкурса")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📜 Правила розыгрыша iPhone 17</b>\n\n"
        "• Каждый платёж 99 ₽ даёт 1 базовый билет + возможность пройти квиз.\n"
        "• Результаты квиза даруют бонусные билеты:\n"
        "  — 10/10 правильных: +3 бонусных билета\n"
        "  — 9/10 правильных: +2 бонусных билета\n"
        "  — 8/10 правильных: +1 бонусный билет\n"
        "• Сбор билетов завершается при достижении 2500 билетов или 10 апреля 2026.\n"
        "• Победитель будет выбран в прямом эфире в канале @mozgo_boy с помощью сервиса https://www.random.org/\n\n"
        "<b>Организатор:</b> Частное лицо ИНН 470102947100 (самозанятый).\n"
        "Поддержка: alexandr@cbda.ru"
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
@router.message(F.text == "👤 Мои заявки")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть в Квиз за iPhone 17» в главном меню!")
    else:
        text = "<b>Твои билеты для участия в розыгрыше:</b>\n\n"
        for t_num, t_type, status, score in apps:
            type_str = "Базовый" if t_type == "base" or t_type == "paid" else "Бонусный"
            score_str = f" ({score}/10)" if score is not None else ""
            text += f"🎟️ Ticket №{t_num:05d} — {type_str}{score_str}\n"
        text += "\nВсе твои билеты участвуют в финальном розыгрыше в прямом эфире!"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
@router.message(F.text == "📊 Лидерборд")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд пока пуст.")
        return

    text = "🏆 <b>Топ-20 участников по количеству билетов:</b>\n\n"
    for i, (username, full_name, ticket_count) in enumerate(leaders, 1):
        name = f"@{username}" if username else full_name
        text += f"{i}. {name} — <b>{ticket_count}</b> билетов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
@router.message(F.text == "📞 Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку по электронной почте alexandr@cbda.ru или в личные сообщения.")
