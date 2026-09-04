from db.db import (
    add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure,
    get_user_applications, has_accepted_rules, mark_rules_accepted
)
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
            "Добро пожаловать в викторину с розыгрышем «iPhone 17»!\n\n"
            "Для участия вам необходимо ознакомиться с правилами.\n\n"
            "«Я ознакомлен с <a href='https://cbda.ru/rules/base'>правилами викторины</a> и согласен с их условиями, "
            "включая обработку моих данных (Telegram ID, username, результаты) в целях проведения викторины. "
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
        f"<b>Добро пожаловать в платную развлекательную викторину с розыгрышем iPhone 17!</b>\n\n"
        "Каждый платёж 99 ₽ дает 1 гарантированный базовый билет + возможность получить до +3 бонусных билетов за хороший результат в квизе.\n\n"
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
        "<b>Спасибо! Теперь вы можете участвовать в викторине.</b>\n\n"
        "Нажмите «🎁 Играть в Квиз за iPhone 17», чтобы приобрести билет и ответить на вопросы.\n\n"
        f"{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    try:
        await callback.message.delete()
    except Exception:
        pass

@router.message(F.text == "📜 Правила розыгрыша")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📌 Правила и условия розыгрыша «iPhone 17»</b>\n\n"
        "<b>Тематика квиза:</b> общеобразовательные вопросы, логика, история, технологии.\n"
        "<b>Приз:</b> Смартфон iPhone 17 (один экземпляр).\n"
        "<b>Стоимость билета:</b> 99 ₽ (1 базовый билет).\n"
        "<b>Бонусные билеты:</b>\n"
        "  - 10/10 правильных ответов → +3 бонусных билета\n"
        "  - 9/10 правильных ответов → +2 бонусных билета\n"
        "  - 8/10 правильных ответов → +1 бонусный билет\n\n"
        "<b>Окончание приёма:</b> при достижении 2500 билетов или 10 апреля 2026 г.\n"
        "<b>Розыгрыш:</b> проводится честно в прямом эфире в канале @mozgo_boy среди всех выданных билетов с помощью https://www.random.org/\n\n"
        "Подробные правила: https://cbda.ru/rules/base\n"
        "<b>Организатор:</b> Частное лицо ИНН 470102947100 (самозанятый)."
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть в Квиз за iPhone 17»!")
    else:
        text = "<b>Твои билеты для участия в розыгрыше iPhone 17:</b>\n\n"
        for t_num, status, score, t_type in apps:
            type_label = "Базовый" if t_type == "base" else ("Бонусный" if t_type == "bonus" else "Платный")
            score_str = f" (Результат: {score}/10)" if score is not None else ""
            text += f"🎫 №{t_num:05d} — {type_label}{score_str}\n"
        text += "\nВсе твои билеты участвуют в итоговом честном розыгрыше!"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд участников пока пуст.")
        return

    text = "🏆 <b>Топ-20 участников по количеству билетов:</b>\n\n"
    for i, (username, full_name, ticket_count) in enumerate(leaders, 1):
        name = f"@{username}" if username else full_name
        text += f"{i}. {name} — <b>{ticket_count}</b> билетов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота по электронной почте alexandr@cbda.ru")
