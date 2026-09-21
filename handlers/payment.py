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
@payment_router.message(F.text == "💰 Поддержать (99 ₽)")
async def play_quiz_handler(message: Message):
    user_id = message.from_user.id

    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer(CLOSED_MESSAGE)
        return

    desc_text = (
        "<b>Квиз за iPhone 17!</b> 📱\n\n"
        "За каждый платёж 99 ₽ вы получаете:\n"
        "• <b>1 гарантированный базовый билет</b>\n"
        "• До <b>+3 бонусных билетов</b> за правильные ответы в квизе:\n"
        "  — 10/10 правильных: +3 билета\n"
        "  — 9/10 правильных: +2 билета\n"
        "  — 8/10 правильных: +1 билет\n\n"
        "Нажмите кнопку ниже для оплаты 99 ₽:"
    )

    await message.answer(
        desc_text,
        reply_markup=get_pay_keyboard(),
        parse_mode="HTML"
    )

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    if not await has_accepted_rules(user_id):
        await callback.message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await callback.message.answer(CLOSED_MESSAGE)
        return

    try:
        await callback.message.answer_invoice(
            title="Квиз за iPhone 17 (попытка)",
            description="1 гарантированный базовый билет + до +3 бонусных билетов за квиз.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Попытка в квизе", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка при генерации счёта: {e}")

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
        pay_text = (
            f"🎉 <b>Оплата прошла!</b> Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз, выбирайте время и место, "
            "чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению. "
            "При закрытии окна или выходе из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Готовы начать квиз?"
        )
        await message.answer(pay_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета.")

    await check_and_trigger_closure(message.bot)
