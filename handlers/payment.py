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
async def play_quiz_request(message: Message):
    user_id = message.from_user.id

    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer(CLOSURE_TEXT)
        return

    text = (
        "🎉 <b>Платный развлекательный квиз за 99 ₽ с розыгрышем iPhone 17</b>\n\n"
        "Каждый платёж 99 ₽ даёт <b>1 гарантированный базовый билет</b> + возможность получить до <b>+3 бонусных билетов</b> за результат в квизе (8, 9 или 10 из 10).\n\n"
        "Нажми кнопку ниже, чтобы оплатить 99 ₽:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await has_accepted_rules(user_id):
        await callback.answer("Примите правила в меню /start", show_alert=True)
        return

    if await is_collection_closed():
        await callback.answer()
        await callback.message.answer(CLOSURE_TEXT)
        return

    await callback.answer()
    try:
        await callback.message.answer_invoice(
            title="Квиз за iPhone 17",
            description="Участие в квизе и 1 гарантированный базовый билет.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие", amount=9900)],
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

    ticket_num = await issue_ticket(user_id, "paid", status="pending")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        text = (
            f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен\n\n"
            "⚠️ <b>Внимание!</b> При прохождении квиза выбирай время и место с устойчивым интернетом. "
            "На каждый вопрос даётся 30 секунд. Готов начать?"
        )
        await message.answer(text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при выдаче билета.")

    await check_and_trigger_closure(message.bot)
