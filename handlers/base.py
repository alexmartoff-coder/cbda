from db.db import (
    add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure,
    get_user_applications, has_accepted_rules, mark_rules_accepted, DB_PATH
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
            "Добро пожаловать в интеллектуальный развлекательный квиз «iPhone 17»!\n\n"
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
        if progress:
            await message.answer(f"{progress}\n\nИспользуйте меню для навигации.", reply_markup=kb, parse_mode="HTML")
        else:
            await message.answer("Используйте кнопку ниже, чтобы принять правила.", reply_markup=kb, parse_mode="HTML")
        return

    kb, progress = await get_main_menu_keyboard(user_id)

    await message.answer(
        f"<b>Добро пожаловать в развлекательный квиз «iPhone 17»!</b>\n\n"
        "Каждое участие стоит 99 ₽.\n"
        "Вы получаете 1 гарантированный базовый билет + возможность получить до +3 бонусных билетов за хорошие результаты в квизе!\n\n"
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
        "Нажмите кнопку в меню, чтобы начать игру!\n\n"
        f"{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    try:
        await callback.message.delete()
    except:
        pass

@router.message(F.text == "📜 Правила розыгрыша")
@router.message(F.text == "❓ Правила конкурса")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📜 Правила розыгрыша iPhone 17</b>\n\n"
        "1. Каждое участие (квиз) стоит <b>99 ₽</b>.\n"
        "2. За каждый платёж ты гарантированно получаешь <b>1 базовый билет</b>.\n"
        "3. В процессе прохождения квиза из 10 вопросов у тебя есть шанс получить бонусные билеты:\n"
        "   • <b>10 правильных ответов</b> → +3 бонусных билета\n"
        "   • <b>9 правильных ответов</b> → +2 бонусных билета\n"
        "   • <b>8 правильных ответов</b> → +1 бонусный билет\n"
        "   • Меньше 8 правильных ответов → бонусов нет\n"
        "4. Сбор билетов останавливается автоматически при достижении лимита в <b>2500 билетов</b> или <b>10 апреля 2026 г.</b>\n"
        "5. Победитель будет выбран абсолютно честно в прямом эфире с использованием генератора случайных чисел <a href='https://www.random.org/'>Random.org</a> среди всех выданных билетов в канале @mozgo_boy.\n\n"
        "Желаем удачи!"
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
@router.message(F.text == "🎫 Мои билеты")
@router.message(F.text == "👤 Мои заявки")
async def cmd_my_tickets(message: Message):
    # The '🎫 Мои билеты' command displays a list of user tickets with numbers (№XXXXX) that are eligible for the draw.
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Начни игру кнопкой в меню!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        for t_num, status, score in apps:
            text += f"🎫 №{t_num:05d} (результат в квизе: {score}/10)\n"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
@router.message(F.text == "📊 Лидерборд")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд пока пуст.")
        return

    text = "🏆 <b>Топ-20 участников по количеству билетов:</b>\n\n"
    for i, (username, full_name, total_tickets) in enumerate(leaders, 1):
        name = f"@{username}" if username else full_name
        text += f"{i}. {name} — <b>{total_tickets}</b> билетов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
@router.message(F.text == "📞 Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота: @mozgo_boy или по электронной почте alexandr@cbda.ru")

@router.message(F.text == "🔄 Обновить данные")
async def cmd_refresh(message: Message):
    user_id = message.from_user.id
    kb, progress = await get_main_menu_keyboard(user_id)
    await message.answer(f"🔄 Данные обновлены!\n\n{progress}", reply_markup=kb, parse_mode="HTML")
