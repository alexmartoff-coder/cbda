from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from database.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def show_mechanics(message: Message):
    from database.db import has_accepted_rules
    if not await has_accepted_rules(message.from_user.id):
        await message.answer("Пожалуйста, примите правила розыгрыша в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!",
            parse_mode="HTML"
        )
        return

    text = (
        "<b>Как участвовать в розыгрыше iPhone 17?</b>\n\n"
        "1. Оплати участие — <b>99 ₽</b>\n"
        "2. Получи <b>1 гарантированный билет</b>\n"
        "3. Пройди квиз из 10 вопросов и получи до <b>+3 бонусных билета</b>:\n"
        "— 10 правильных → +3 билета\n"
        "— 9 правильных → +2 билета\n"
        "— 8 правильных → +1 билет\n\n"
        "Чем больше билетов, тем выше шансы!"
    )
    from keyboards.menu import get_pay_keyboard
    await message.answer(text, reply_markup=get_pay_keyboard(), parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment_callback(callback: CallbackQuery):
    await callback.answer()
    message = callback.message
    user_id = callback.from_user.id

    if await is_collection_closed():
        await message.answer("🎉 Сбор билетов завершён!")
        return

    try:
        await callback.bot.send_invoice(
            chat_id=user_id,
            title="Участие в квизе iPhone 17",
            description="1 базовый билет + бонусы за квиз",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await message.answer(f"❌ Ошибка при формировании счёта. Попробуйте позже.")

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
            "⚠️ <b>Внимание!</b> Выбирай время и место, чтобы интернет был устойчивым. "
            "Отсутствие ответа или закрытие приложения будет засчитано как неправильный ответ.\n\n"
            "Готов начать квиз за бонусные билеты?"
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета. Обратитесь в поддержку.")

    await check_and_trigger_closure(message.bot)
