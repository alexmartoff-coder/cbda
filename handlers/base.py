from database.db import (
    add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure,
    get_user_applications, has_accepted_rules, mark_rules_accepted
)
import aiosqlite
from keyboards.menu import get_main_menu_keyboard, get_rules_agreement_keyboard, get_pay_keyboard
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
        "Каждый платёж (99 ₽) даёт 1 базовый билет + возможность получить до +3 бонусных билетов за хороший результат в квизе.\n\n"
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
        "Нажмите кнопку «🎁 Играть в Квиз за iPhone 17» в меню ниже.",
        reply_markup=kb,
        parse_mode="HTML"
    )
    try:
        await callback.message.delete()
    except:
        pass

@router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def cmd_play_flow(message: Message):
    user_id = message.from_user.id

    if await is_collection_closed():
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    mechanics_text = (
        "<b>Как это работает?</b>\n\n"
        "1️⃣ Вы оплачиваете 99 ₽.\n"
        "2️⃣ Сразу получаете <b>1 базовый билет</b>.\n"
        "3️⃣ Проходите квиз из 10 вопросов.\n"
        "4️⃣ Получаете <b>бонусные билеты</b> за правильные ответы:\n"
        "   • 10 верных → <b>+3 билета</b>\n"
        "   • 9 верных → <b>+2 билета</b>\n"
        "   • 8 верных → <b>+1 билет</b>\n\n"
        "Все билеты участвуют в финальном розыгрыше iPhone 17!"
    )
    await message.answer(mechanics_text, reply_markup=get_pay_keyboard(), parse_mode="HTML")

@router.message(F.text == "📜 Правила розыгрыша")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📜 Правила розыгрыша iPhone 17</b>\n\n"
        "1. <b>Общие положения</b>\n"
        "Квиз является развлекательным мероприятием с элементами интеллектуального конкурса.\n\n"
        "2. <b>Участие</b>\n"
        "Стоимость участия — 99 ₽ за одну попытку.\n"
        "Каждая попытка включает 1 базовый билет и сессию квиза.\n\n"
        "3. <b>Начисление билетов</b>\n"
        "• Базовый билет: выдаётся сразу после оплаты.\n"
        "• Бонусные билеты: зависят от результата квиза (8, 9 или 10 правильных ответов).\n\n"
        "4. <b>Завершение сбора</b>\n"
        "Сбор билетов останавливается при достижении 2500 билетов или 10 апреля 2026 г.\n\n"
        "5. <b>Определение победителя</b>\n"
        "Победитель выбирается честно с помощью генератора случайных чисел (random.org) среди всех выданных билетов в прямом эфире канала @mozgo_boy.\n\n"
        "Полные правила: <a href='https://cbda.ru/rules/base'>cbda.ru/rules/base</a>"
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть», чтобы получить первый билет!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        for t_num, t_type, status, score in apps:
            t_type_name = "Базовый" if t_type == "base" else "Бонусный"
            if status == "pending":
                status_text = "⏳ Ожидает квиза"
            else:
                status_text = "✅ Участвует в розыгрыше"

            text += f"🎫 №{t_num:05d} ({t_type_name}) — {status_text}\n"

        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд пока пуст. Стань первым!")
        return

    text = "🏆 <b>Топ-20 участников по количеству билетов:</b>\n\n"
    for i, (username, full_name, ticket_count) in enumerate(leaders, 1):
        name = username if username else full_name
        text += f"{i}. {name} — <b>{ticket_count}</b> билетов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота по адресу: alexandr@cbda.ru")

@router.message(F.text == "🔄 Обновить данные")
async def cmd_refresh(message: Message):
    user_id = message.from_user.id
    kb, progress = await get_main_menu_keyboard(user_id)
    await message.answer(f"🔄 Данные обновлены!\n\n{progress}", reply_markup=kb, parse_mode="HTML")
