from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment, has_accepted_rules
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

CLOSURE_TEXT = (
    "🎉 Сбор билетов завершён досрочно!\n\n"
    "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
    "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
    "Следи за обновлениями!"
)

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
@payment_router.message(F.text == "💰 Поддержать (99 ₽)")
async def show_mechanics(message: Message):
    user_id = message.from_user.id

    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer(CLOSURE_TEXT)
        return

    text = (
        "📱 <b>Квиз за iPhone 17 PRO 256 Гб</b>\n\n"
        "Стоимость участия: <b>99 ₽</b>\n\n"
        "Каждая оплата даёт:\n"
        "• 1 гарантированный базовый билет\n"
        "• Квиз из 10 вопросов на тему Apple\n"
        "• До +3 бонусных билетов за отличный результат:\n"
        "  🎯 10/10 — <b>+3 бонусных билета</b>\n"
        "  🎯 9/10 — <b>+2 бонусных билета</b>\n"
        "  🎯 8/10 — <b>+1 бонусный билет</b>\n\n"
        "Нажмите кнопку ниже, чтобы оплатить 99 ₽."
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])

    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    if not await has_accepted_rules(user_id):
        await callback.message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await callback.message.answer(CLOSURE_TEXT)
        return

    try:
        await callback.message.answer_invoice(
            title="Квиз iPhone 17 (99 ₽)",
            description="1 гарантированный билет + до +3 бонусных билетов за квиз",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Оплата участия", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка при создании счёта: {e}")

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

    ticket_num = await issue_ticket(user_id, "paid", status="pending")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        text = (
            f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> При прохождении квиза выбирай место с устойчивым интернетом. "
            "На каждый вопрос даётся 30 секунд.\n\n"
            "Готов пройти квиз?"
        )
        await message.answer(text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета.")

    await check_and_trigger_closure(message.bot)
