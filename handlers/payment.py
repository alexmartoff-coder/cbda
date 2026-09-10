from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment, has_accepted_rules
from keyboards.menu import get_start_quiz_keyboard, get_pay_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def handle_play_button(message: Message):
    user_id = message.from_user.id

    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
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

    mechanic_text = (
        "<b>Квиз за iPhone 17</b>\n\n"
        "Каждый платёж 99 ₽ даёт:\n"
        "• 1 гарантированный базовый билет\n"
        "• До +3 бонусных билетов за хороший результат в квизе (8, 9 или 10 правильных ответов)\n\n"
        "Нажми «Оплатить 99 ₽», чтобы получить билет и пройти квиз!"
    )
    await message.answer(mechanic_text, reply_markup=get_pay_keyboard(), parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not await has_accepted_rules(user_id):
        await callback.answer("Примите правила перед оплатой!", show_alert=True)
        return

    if await is_collection_closed():
        await callback.answer("Сбор билетов завершён!", show_alert=True)
        closure_text = (
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        await callback.message.answer(closure_text)
        return

    await callback.answer()
    await callback.message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        await callback.message.answer_invoice(
            title="Квиз за iPhone 17",
            description="Базовый билет + участие в квизе на бонусные билеты.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие в квизе", amount=9900)],
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

    ticket_num = await issue_ticket(user_id, "base")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=1, is_active=True)
        pay_success_text = (
            f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "Готов пройти квиз из 10 вопросов и заработать до +3 бонусных билетов?"
        )
        await message.answer(pay_success_text, reply_markup=get_start_quiz_keyboard())
    else:
        await message.answer("Ошибка при выдаче билета. Обратитесь в поддержку.")

    await check_and_trigger_closure(message.bot)
