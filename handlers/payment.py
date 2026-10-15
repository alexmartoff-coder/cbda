from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard, get_pay_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
@payment_router.message(F.text == "💰 Поддержать (99 ₽)")
async def show_quiz_play_info(message: Message):
    user_id = message.from_user.id
    from db.db import has_accepted_rules
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

    text = (
        "📱 <b>Платный развлекательный квиз за 99 ₽ с розыгрышем iPhone 17!</b>\n\n"
        "Каждый платёж даёт 1 гарантированный базовый билет + возможность получить до +3 бонусных билетов за результат в квизе:\n"
        "• 10 правильных ответов → +3 бонусных билета\n"
        "• 9 правильных ответов → +2 бонусных билета\n"
        "• 8 правильных ответов → +1 бонусный билет\n"
        "• Меньше 8 → бонусов нет\n\n"
        "Жми кнопку ниже, чтобы оплатить 99 ₽ и получить билет!"
    )
    await message.answer(text, reply_markup=get_pay_keyboard(), parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    user_id = callback.from_user.id
    from db.db import has_accepted_rules
    if not await has_accepted_rules(user_id):
        await callback.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.", show_alert=True)
        return

    if await is_collection_closed():
        await callback.answer("🎉 Сбор билетов завершён!", show_alert=True)
        await callback.message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    await callback.answer()
    await callback.message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        await callback.message.answer_invoice(
            title="Квиз за iPhone 17 + попытка",
            description="Платная попытка в квизе с розыгрышем iPhone 17.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Билет на квиз", amount=9900)],
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
    await message.answer("✅ Оплата прошла успешно!")

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
        warning_text = (
            f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> Когда будешь проходить квиз, выбирай время и место с устойчивым интернетом. "
            "Квиз состоит из 10 вопросов с таймером 30 секунд на каждый. "
            "При закрытии окна или выходе из приложения отсутствие ответов засчитывается как проигрыш.\n\n"
            "Готов пройти квиз?"
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета.")

    await check_and_trigger_closure(message.bot)
