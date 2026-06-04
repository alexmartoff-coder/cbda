from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from database.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def play_button_handler(message: Message):
    user_id = message.from_user.id

    from database.db import has_accepted_rules
    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    # Предлагаем оплату
    text = (
        "<b>Как это работает?</b>\n\n"
        "1. Оплачиваешь 99 ₽\n"
        "2. Получаешь 1 гарантированный базовый билет\n"
        "3. Проходишь квиз (10 вопросов)\n"
        "4. За правильные ответы получаешь бонусные билеты:\n"
        "   — 10 верных → +3 билета\n"
        "   — 9 верных → +2 билета\n"
        "   — 8 верных → +1 билет\n\n"
        "Все билеты участвуют в розыгрыше iPhone 17!"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])

    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def process_pay_callback(callback: CallbackQuery):
    await callback.answer()
    message = callback.message

    if await is_collection_closed():
        await message.answer("🎉 Приём заявок завершён!")
        return

    try:
        await message.answer_invoice(
            title="Поддержка конкурса + попытка",
            description="Дополнительная попытка в конкурсе iPhone 17 PRO 256 Гб.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Поддержка", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await message.answer(f"❌ Ошибка: {e}")

@payment_router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@payment_router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    user_id = message.from_user.id
    user = message.from_user

    await add_user(user_id, user.username, user.full_name)

    sp = message.successful_payment
    await log_payment(
        user_id,
        sp.total_amount // 100,
        sp.invoice_payload,
        sp.telegram_payment_charge_id,
        sp.provider_payment_charge_id
    )

    ticket_num = await issue_ticket(user_id, "paid")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        await message.answer(
            f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "Нажми кнопку ниже, чтобы начать квиз.",
            reply_markup=get_start_quiz_keyboard()
        )
    else:
        await message.answer("Ошибка при создании платной заявки.")

    await check_and_trigger_closure(message.bot)
