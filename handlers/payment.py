import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
import config
from db.db import (
    add_user, issue_ticket, set_quiz_session, is_collection_closed,
    check_and_trigger_closure, log_payment, has_accepted_rules
)
from keyboards.menu import get_pay_99_keyboard, get_start_quiz_keyboard

payment_router = Router(name="payment_router")

CLOSED_MESSAGE = (
    "🎉 Сбор билетов завершён досрочно!\n\n"
    "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
    "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
    "Следи за обновлениями!"
)

MECHANIC_DESCRIPTION = (
    "<b>Правила и механика квиза:</b>\n\n"
    "• Каждый платёж 99 ₽ дает <b>1 гарантированный базовый билет</b>.\n"
    "• Далее проходит квиз из <b>10 вопросов</b> (30 секунд на вопрос).\n"
    "• За хороший результат в квизе можно получить дополнительные бонусные билеты:\n"
    "  - <b>10 правильных ответов</b> → +3 бонусных билета\n"
    "  - <b>9 правильных ответов</b> → +2 бонусных билета\n"
    "  - <b>8 правильных ответов</b> → +1 бонусный билет\n"
    "  - Меньше 8 → бонусных билетов нет.\n\n"
    "Нажмите кнопку ниже, чтобы перейти к оплате 99 ₽."
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

    await message.answer(MECHANIC_DESCRIPTION, reply_markup=get_pay_99_keyboard(), parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    await callback.answer()
    if await is_collection_closed():
        await callback.message.answer(CLOSED_MESSAGE)
        return

    if not config.YOOKASSA_PROVIDER_TOKEN:
        await callback.message.answer("❌ Платёжная система временно недоступна (отсутствует токен провайдера).")
        return

    try:
        await callback.message.answer_invoice(
            title="Билет на квиз iPhone 17",
            description="1 базовый билет + возможность получить до +3 бонусных билетов в квизе.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие в квизе", amount=9900)],
            payload="ticket_purchase_99"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка формирования счёта: {e}")

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

    ticket_num = await issue_ticket(user_id, "base", status="pending")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        text = (
            f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> При прохождении квиза выбирай время и место с устойчивым интернетом. "
            "На каждый вопрос даётся 30 секунд. Готов начать?"
        )
        await message.answer(text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при выдаче билета. Пожалуйста, обратитесь в поддержку.")

    await check_and_trigger_closure(message.bot)
