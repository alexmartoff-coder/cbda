import aiosqlite
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from db.db import (
    add_user, is_collection_closed, check_and_trigger_closure,
    has_accepted_rules, mark_rules_accepted, get_user_applications, get_leaderboard
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
            "Добро пожаловать в интеллектуальный конкурс «iPhone 17»! 📱\n\n"
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
    welcome_text = (
        "<b>Добро пожаловать в интеллектуальный квиз за iPhone 17!</b> 📱\n\n"
        "Каждый платёж за 99 ₽ даёт 1 гарантированный базовый билет + возможность получить до +3 бонусных билетов за хороший результат в квизе (8/9/10 правильных ответов).\n\n"
        "Всего за одну попытку можно получить до 4 билетов!\n\n"
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
        "<b>Добро пожаловать в интеллектуальный квиз за iPhone 17!</b> 📱\n\n"
        "Каждый платёж за 99 ₽ даёт 1 гарантированный базовый билет + возможность получить до +3 бонусных билетов за хороший результат в квизе (8/9/10 правильных ответов).\n\n"
        "Всего за одну попытку можно получить до 4 билетов!\n\n"
        f"{progress}"
    )
    await callback.message.answer(welcome_text, reply_markup=kb, parse_mode="HTML")
    try:
        await callback.message.delete()
    except:
        pass

@router.message(F.text == "📜 Правила розыгрыша")
@router.message(F.text == "❓ Правила конкурса")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📌 Правила интеллектуального квиза «iPhone 17»</b>\n\n"
        "Интеллектуальный квиз «iPhone 17»\n"
        "<b>Тематика квиза:</b> компания Apple, её устройства, операционные системы, технологии, история.\n"
        "<b>Приз:</b> iPhone 17 (один экземпляр).\n"
        "<b>Стоимость попытки:</b> 99 ₽.\n"
        "Каждый платёж даёт 1 гарантированный базовый билет + возможность получить до +3 бонусных билетов за хороший результат в квизе (8/9/10 правильных ответов).\n\n"
        "<b>Количество билетов для завершения:</b> 2500.\n"
        "<b>Окончание приёма билетов:</b> автоматически при достижении 2500 билетов или 10 апреля 2026.\n"
        "<b>Розыгрыш:</b> проводится честно среди всех выданных билетов. Победитель будет выбран путём https://www.random.org/.\n\n"
        "Все остальные условия — в соответствии с Основными правилами интеллектуальных конкурсов, размещённых по ссылке:\n"
        "https://cbda.ru/rules/base\n\n"
        "Участие в конкурсе означает полное согласие с правилами и условиями обработки данных."
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
@router.message(F.text == "👤 Мои заявки")
async def cmd_my_tickets(message: Message):
    user_id = message.from_user.id
    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса перед просмотром билетов.")
        return

    apps = await get_user_applications(user_id)
    if not apps:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть в Квиз за iPhone 17» в меню, чтобы получить первый билет!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        for t_num, status, score in apps:
            text += f"🎫 №{t_num:05d} — Участвует в розыгрыше! ✅\n"
        text += f"\nВсего у тебя билетов: <b>{len(apps)}</b>"
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
    await message.answer(
        "📞 <b>Служба поддержки</b>\n\n"
        "По всем вопросам обращайтесь в поддержку бота по электронной почте: alexandr@cbda.ru",
        parse_mode="HTML"
    )

@router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def cmd_play(message: Message):
    user_id = message.from_user.id
    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню перед участием.")
        return

    if await is_collection_closed():
        closure_text = (
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        await message.answer(closure_text)
        return

    mechanics_desc = (
        "Добро пожаловать в интеллектуальный квиз за iPhone 17! 📱\n\n"
        "Стоимость участия составляет всего 99 ₽. За эту сумму ты гарантированно получаешь 1 базовый билет участника розыгрыша.\n\n"
        "Но это ещё не всё! Сразу после оплаты у тебя будет возможность пройти увлекательный квиз из 10 вопросов про компанию Apple и получить дополнительные бонусные билеты:\n"
        "🏆 10 правильных ответов → +3 бонусных билета!\n"
        "🥈 9 правильных ответов → +2 бонусных билета!\n"
        "🥉 8 правильных ответов → +1 бонусный билет!\n\n"
        "Всего за одну попытку можно получить до 4 билетов, что значительно увеличит твои шансы на победу!\n\n"
        "Нажми на кнопку ниже, чтобы оплатить участие и начать квиз."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])

    await message.answer(mechanics_desc, reply_markup=kb)
