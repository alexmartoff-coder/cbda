from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from db.db import (
    add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure,
    log_payment, has_accepted_rules, DB_PATH
)
from keyboards.menu import get_start_quiz_keyboard
import config
import logging
import aiosqlite

payment_router = Router(name="payment_router")

def get_closure_text():
    return (
        "🎉 Сбор билетов завершён досрочно!\n\n"
        "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
        "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
        "Следи за обновлениями!"
    )

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def play_button_handler(message: Message):
    user_id = message.from_user.id

    # 1. Check if rules accepted
    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    # 2. Check if collection closed
    if await is_collection_closed():
        await message.answer(get_closure_text(), parse_mode="HTML")
        return

    # 3. Check if user already has a pending ticket
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT ticket_number FROM tickets WHERE user_id = ? AND status = 'pending' LIMIT 1", (user_id,)) as c:
            row = await c.fetchone()
            pending_ticket = row[0] if row else None

    if pending_ticket:
        await set_quiz_session(user_id, pending_ticket, score=0, current_question=0, is_active=True)
        warning_text = (
            f"У тебя уже есть оплаченный билет №{pending_ticket:05d}, для которого квиз ещё не пройден!\n\n"
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз, выбирайте время и место, чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выходе из приложения отсутствие ответов будет оцениваться как проигрыш в вопросе.\n\n"
            "Нажми кнопку ниже, чтобы запустить квиз (10 вопросов)."
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
        return

    # 4. Show mechanic description
    mechanics_html = (
        "🎁 <b>Игра за iPhone 17!</b>\n\n"
        "Каждый платёж даёт:\n"
        "• <b>1 гарантированный базовый билет</b>\n"
        "• Возможность получить до <b>+3 бонусных билетов</b> за хороший результат в квизе:\n"
        "  - 10 правильных ответов: <b>+3 бонусных билета</b>\n"
        "  - 9 правильных ответов: <b>+2 бонусных билета</b>\n"
        "  - 8 правильных ответов: <b>+1 бонусный билет</b>\n\n"
        "Стоимость участия: <b>99 ₽</b>.\n\n"
        "Нажмите на кнопку ниже, чтобы перейти к оплате."
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    pay_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])

    await message.answer(mechanics_html, reply_markup=pay_keyboard, parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await has_accepted_rules(user_id):
        await callback.answer("Пожалуйста, примите правила!", show_alert=True)
        return

    if await is_collection_closed():
        await callback.answer("Сбор билетов завершён!", show_alert=True)
        await callback.message.answer(get_closure_text(), parse_mode="HTML")
        return

    await callback.answer()
    await callback.message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        await callback.message.answer_invoice(
            title="Участие в квизе за iPhone 17",
            description="Оплата участия и получение базового билета + доступ к квизу.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие в квизе", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка: {e}")

@payment_router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@payment_router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    user_id = message.from_user.id
    user = message.from_user

    await add_user(user_id, user.username, user.full_name)
    await message.answer("✅ Оплата прошла успешно!")

    sp = message.successful_payment
    await log_payment(
        user_id,
        sp.total_amount // 100,
        sp.invoice_payload,
        sp.telegram_payment_charge_id,
        sp.provider_payment_charge_id
    )

    # Issue base ticket with status='pending'
    ticket_num = await issue_ticket(user_id, "base", status="pending")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        warning_text = (
            f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз, выбирайте время и место, чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выходе из приложения отсутствие ответов будет оцениваться как проигранные вопросы.\n\n"
            "Нажми кнопку ниже, чтобы запустить квиз (10 вопросов)."
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании базового билета.")

    await check_and_trigger_closure(message.bot)
