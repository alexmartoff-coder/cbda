from db.db import (
    add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure,
    get_user_applications, has_accepted_rules, mark_rules_accepted
)
import aiosqlite
from keyboards.menu import get_main_menu_keyboard, get_rules_agreement_keyboard
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
            "Для участия необходимо ознакомиться с правилами.\n\n"
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
    welcome_text = (
        "<b>Добро пожаловать в платный развлекательный квиз за 99 ₽ с розыгрышем iPhone 17! 📱</b>\n\n"
        "Каждый платёж даёт 1 гарантированный базовый билет + возможность получить до +3 бонусных билетов за прохождение квиза.\n\n"
        f"{progress}"
    )
    await message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "accept_rules")
async def accept_rules_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    await mark_rules_accepted(user_id)
    await callback.answer("✅ Правила приняты!")

    kb, progress = await get_main_menu_keyboard(user_id)
    welcome_text = (
        "<b>Спасибо! Теперь вы можете участвовать в конкурсе.</b>\n\n"
        "Каждый платёж 99 ₽ даёт 1 гарантированный базовый билет + до +3 бонусных билетов за правильные ответы в квизе.\n\n"
        f"{progress}"
    )
    await callback.message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")
    try:
        await callback.message.delete()
    except Exception:
        pass

@router.message(F.text == "📜 Правила розыгрыша")
@router.message(F.text == "❓ Правила конкурса")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📜 Правила розыгрыша iPhone 17</b>\n\n"
        "<b>Тематика квиза:</b> Технологии, бренд Apple и устройства.\n"
        "<b>Приз:</b> iPhone 17 (один экземпляр).\n"
        "<b>Механика:</b> Каждый платёж 99 ₽ выдаёт 1 базовый билет и запускает 10 вопросов квиза.\n"
        "<b>Бонусные билеты:</b>\n"
        "• 10 верных ответов: <b>+3 бонусных билета</b>\n"
        "• 9 верных ответов: <b>+2 бонусных билета</b>\n"
        "• 8 верных ответов: <b>+1 бонусный билет</b>\n"
        "• Менее 8: бонусов нет.\n\n"
        "<b>Лимит:</b> Сбор билетов завершается при достижении 2500 билетов или 10 апреля 2026 г.\n"
        "<b>Определение победителя:</b> Победитель выбирается с помощью сервиса https://www.random.org/ в прямом эфире в канале @mozgo_boy.\n\n"
        "Организатор: Частное лицо ИНН 470102947100 (самозанятый).\n"
        "Полные правила: https://cbda.ru/rules/base"
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
@router.message(F.text == "👤 Мои заявки")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У вас пока нет билетов. Нажмите «🎁 Играть в Квиз за iPhone 17» в главном меню!")
    else:
        text = "<b>🎟️ Ваши билеты:</b>\n\n"
        for t_num, t_type, status, score in apps:
            type_label = "Базовый" if t_type == "base" else "Бонусный"
            score_text = f" (Квиз: {score}/10)" if score is not None else ""
            text += f"🎫 №{t_num:05d} — {type_label}{score_text}\n"
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
        name = f"@{username}" if username else (full_name if full_name else "Участник")
        text += f"{i}. {name} — <b>{ticket_count}</b> билетов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
@router.message(F.text == "📞 Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота по электронной почте: alexandr@cbda.ru")
