from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment, has_accepted_rules
from keyboards.menu import get_start_quiz_keyboard, get_pay_inline_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def quiz_button_handler(message: Message):
    user_id = message.from_user.id

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

    mechanic_text = (
        "🧠 <b>Платный развлекательный квиз за 99 ₽ с розыгрышем iPhone 17</b>\n\n"
        "<b>Как это работает:</b>\n"
        "• Каждый платёж 99 ₽ дает <b>1 гарантированный базовый билет</b>.\n"
        "• Отвечай на 10 вопросов квиза и получай <b>бонусные билеты</b> за отличный результат:\n"
        "  — 10 правильных ответов: <b>+3 бонусных билета</b>\n"
        "  — 9 правильных ответов: <b>+2 бонусных билета</b>\n"
        "  — 8 правильных ответов: <b>+1 бонусный билет</b>\n"
        "  — меньше 8 ответов: бонусов нет.\n\n"
        "Сбор билетов остановится при достижении 2500 билетов или 10 апреля 2026.\n"
        "Розыгрыш проводиться среди всех выданных билетов через random.org!"
    )
    await message.answer(mechanic_text, reply_markup=get_pay_inline_keyboard(), parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    await callback.answer()

    if await is_collection_closed():
        await callback.message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    try:
        await callback.message.answer_invoice(
            title="Участие в квизе iPhone 17",
            description="1 базовый билет + шанс получить до +3 бонусных билетов",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Билет на квиз", amount=9900)],
            payload="quiz_ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка при генерации счета: {e}")

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
        text = (
            f"Оплата прошла! Твой базовый билет <b>№{ticket_num:05d}</b> получен.\n\n"
            "Нажми <b>«Начать квиз»</b>, чтобы ответить на 10 вопросов и получить дополнительные бонусные билеты!"
        )
        await message.answer(text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета.")

    await check_and_trigger_closure(message.bot)
