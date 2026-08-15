from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

CLOSED_MESSAGE = (
    "🎉 Сбор билетов завершён досрочно!\n\n"
    "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
    "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
    "Следи за обновлениями!"
)

@payment_router.message(F.text.in_({"🎁 Играть в Квиз за iPhone 17", "💰 Поддержать (99 ₽)"}))
async def start_quiz_info(message: Message):
    user_id = message.from_user.id

    from db.db import has_accepted_rules
    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer(CLOSED_MESSAGE)
        return

    desc = (
        "<b>🎁 Платный квиз за iPhone 17</b>\n\n"
        "Стоимость участия: <b>99 ₽</b>\n\n"
        "Каждый платёж даёт:\n"
        "• <b>1 гарантированный базовый билет</b>\n"
        "• Возможность получить до <b>+3 бонусных билетов</b> за правильные ответы:\n"
        "  — 10/10 правильных ответов: +3 билета\n"
        "  — 9/10 правильных ответов: +2 билета\n"
        "  — 8/10 правильных ответов: +1 билет\n"
        "  — меньше 8: без бонусов\n\n"
        "Нажмите кнопку ниже для оплаты."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])
    await message.answer(desc, reply_markup=kb, parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    await callback.answer()
    if await is_collection_closed():
        await callback.message.answer(CLOSED_MESSAGE)
        return

    await callback.message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        await callback.message.answer_invoice(
            title="Квиз iPhone 17",
            description="Участие в квизе за iPhone 17",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Оплата квиза", amount=9900)],
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
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        text = f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\nНажми «Начать квиз» для старта!"
        await message.answer(text, reply_markup=get_start_quiz_keyboard())
    else:
        await message.answer("Ошибка при создании билета.")

    await check_and_trigger_closure(message.bot)
