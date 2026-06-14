from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from database.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🆓 Бесплатная заявка на участие")
async def start_free_attempt(message: Message):
    user_id = message.from_user.id

    from database.db import has_accepted_rules
    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer("🎉 Приём заявок завершён!")
        return

    from database.db import has_user_used_free_attempt
    if await has_user_used_free_attempt(user_id):
        await message.answer("Вы уже использовали свою бесплатную попытку.")
        return

    ticket_num = await issue_ticket(user_id, "base")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        warning_text = (
            f"✅ Ваша заявка №{ticket_num:05d} создана.\n\n"
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Готовы пройти квиз?"
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании заявки.")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    message = callback.message
    from database.db import has_accepted_rules
    if not await has_accepted_rules(callback.from_user.id):
        await callback.answer("Примите правила!", show_alert=True)
        return

    if await is_collection_closed():
        await callback.answer("Сбор завершён!", show_alert=True)
        return

    await callback.answer()
    await message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        await message.answer_invoice(
            title="Участие в квизе за iPhone 17",
            description="Оплата участия и получение базового билета.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие", amount=9900)],
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
    await message.answer("✅ Оплата прошла успешно!")

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
        warning_text = (
            f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза.\n\n"
            "Нажми кнопку ниже, чтобы начать квиз."
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета.")

    await check_and_trigger_closure(message.bot)
