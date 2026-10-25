from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment, has_accepted_rules
from keyboards.menu import get_start_quiz_keyboard, get_pay_keyboard
import config
import logging

payment_router = Router(name="payment_router")

CLOSED_MESSAGE = (
    "🎉 Сбор билетов завершён досрочно!\n\n"
    "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
    "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
    "Следи за обновлениями!"
)

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def handle_play_quiz(message: Message):
    user_id = message.from_user.id

    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer(CLOSED_MESSAGE)
        return

    mechanics_text = (
        "🎁 <b>Платный развлекательный квиз за 99 ₽ с розыгрышем iPhone 17</b>\n\n"
        "Каждый платёж дает:\n"
        "• <b>1 гарантированный базовый билет</b>\n"
        "• Возможность получить <b>до +3 бонусных билетов</b> за правильные ответы в квизе:\n"
        "   — 10 правильных ответов: <b>+3 бонусных билета</b>\n"
        "   — 9 правильных ответов: <b>+2 бонусных билета</b>\n"
        "   — 8 правильных ответов: <b>+1 бонусный билет</b>\n"
        "   — Меньше 8: без бонусов\n\n"
        "Нажмите «Оплатить 99 ₽», чтобы получить билет и начать квиз!"
    )
    await message.answer(mechanics_text, reply_markup=get_pay_keyboard(), parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment_callback(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    if await is_collection_closed():
        await callback.message.answer(CLOSED_MESSAGE)
        return

    try:
        await callback.message.answer_invoice(
            title="Билет + Попытка в квизе iPhone 17",
            description="1 базовый билет + участие в квизе с возможностью получить до +3 бонусных билетов.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Билет на квиз", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка при формировании счёта: {e}")

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
        msg_text = (
            f"Оплата прошла! Твой базовый билет №<b>{ticket_num:05d}</b> получен.\n\n"
            "⏱ На каждый вопрос квиза дается 30 секунд.\n"
            "Готовы начать квиз?"
        )
        await message.answer(msg_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при получении билета.")

    await check_and_trigger_closure(message.bot)
