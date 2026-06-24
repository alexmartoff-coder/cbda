from db.db import (
    add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure,
    get_user_applications, issue_ticket, set_quiz_session,
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
            "Добро пожаловать в развлекательный квиз за iPhone 17!\n\n"
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
        f"<b>Добро пожаловать в квиз за iPhone 17!</b>\n\n"
        "Каждый платёж (99 ₽) даёт 1 гарантированный базовый билет + возможность получить до +3 бонусных билетов за хороший результат в квизе.\n\n"
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
        "Нажмите «🎁 Играть в Квиз за iPhone 17», чтобы начать.\n\n"
        f"{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    try:
        await callback.message.delete()
    except:
        pass

@router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def cmd_play_redirect(message: Message):
    if await is_collection_closed():
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    # This will be handled by the payment router if not closed
    # But we include it here just in case of manual button clicks on old keyboards
    from handlers.payment import start_payment
    await start_payment(message)

@router.message(F.text == "📜 Правила розыгрыша")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📌 Правила розыгрыша iPhone 17</b>\n\n"
        "1. Участие в квизе стоит 99 ₽.\n"
        "2. После оплаты вы получаете 1 базовый билет.\n"
        "3. Далее запускается квиз из 10 вопросов.\n"
        "4. Бонусные билеты за результат:\n"
        "   - 10 правильных ответов: +3 билета\n"
        "   - 9 правильных ответов: +2 билета\n"
        "   - 8 правильных ответов: +1 билет\n"
        "5. Сбор билетов останавливается при достижении 2500 билетов или 10 апреля 2026 г.\n"
        "6. Победитель будет выбран в прямом эфире с помощью random.org среди всех выданных билетов.\n\n"
        "Полные правила: https://cbda.ru/rules/base"
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У тебя пока нет билетов. Нажми «🎁 Играть», чтобы получить первый!")
    else:
        text = "<b>Твои билеты:</b>\n\n"
        for t_num, status, score in apps:
            text += f"🎫 №{t_num:05d}\n"

        text += f"\nВсего билетов: {len(apps)}"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard(limit=20)
    if not leaders:
        # If no 'finalist' status tickets yet, show top by total count
        from db.db import DB_PATH
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
    for i, (username, full_name, count) in enumerate(leaders, 1):
        name = username if username else full_name
        text += f"{i}. {name} — <b>{count}</b> билетов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку по адресу: alexandr@cbda.ru")

@router.message(F.text == "🔄 Обновить данные")
async def cmd_refresh(message: Message):
    user_id = message.from_user.id
    kb, progress = await get_main_menu_keyboard(user_id)
    await message.answer(f"🔄 Данные обновлены!\n\n{progress}", reply_markup=kb, parse_mode="HTML")
