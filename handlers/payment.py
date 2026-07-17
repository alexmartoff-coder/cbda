import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment, has_accepted_rules
from keyboards.menu import get_start_quiz_keyboard
import config

payment_router = Router(name="payment_router")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await has_accepted_rules(user_id):
        await callback.answer("Пожалуйста, примите правила конкурса в главном меню перед участием.", show_alert=True)
        return

    if await is_collection_closed():
        await callback.answer("🎉 Приём билетов завершён!", show_alert=True)
        await callback.message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    await callback.answer()
    await callback.message.answer("🧾 Формируем счёт на 99 ₽...")

    try:
        await callback.message.answer_invoice(
            title="Участие в квизе за iPhone 17",
            description="Гарантированный базовый билет + участие в квизе за iPhone 17",
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
    # Mandatory handler to approve transaction requests before YooKassa can process them
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

    ticket_num = await issue_ticket(user_id, "paid", status="pending")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=1, is_active=True)
        await message.answer(f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.")

        warning_text = (
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Готовы пройти квиз?"
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета.")

    await check_and_trigger_closure(message.bot)
