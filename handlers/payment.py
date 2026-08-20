from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment, has_accepted_rules
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def play_button_handler(message: Message):
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

    # Mechanics description with 'Оплатить 99 ₽' inline button
    mechanics_text = (
        "<b>🎁 Квиз с розыгрышем iPhone 17!</b>\n\n"
        "Участие в квизе стоит 99 ₽. За каждый платёж ты гарантированно получаешь:\n"
        "• 🎟️ <b>1 базовый билет</b> для участия в розыгрыше.\n"
        "• 🚀 <b>Возможность пройти квиз из 10 вопросов</b> и получить до 3 дополнительных бонусных билетов за правильные ответы:\n"
        "   - 10 правильных ответов: <b>+3 бонусных билета</b>\n"
        "   - 9 правильных ответов: <b>+2 бонусных билета</b>\n"
        "   - 8 правильных ответов: <b>+1 бонусный билет</b>\n\n"
        "Все твои билеты суммируются и увеличивают шансы на победу!\n"
        "Розыгрыш пройдёт в прямом эфире в канале @mozgo_boy с помощью сервиса random.org."
    )

    pay_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])

    await message.answer(mechanics_text, reply_markup=pay_keyboard, parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await has_accepted_rules(user_id):
        await callback.answer("Пожалуйста, примите правила конкурса.", show_alert=True)
        return

    if await is_collection_closed():
        closure_text = (
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        await callback.message.answer(closure_text)
        await callback.answer()
        return

    try:
        await callback.message.answer_invoice(
            title="Оплата участия в квизе за iPhone 17",
            description="Оплата 99 ₽ для получения 1 базового билета и прохождения квиза.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Оплата участия", amount=9900)],
            payload="ticket_purchase"
        )
        await callback.answer()
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка формирования счета: {e}")
        await callback.answer()

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

    ticket_num = await issue_ticket(user_id, "paid")
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
        await message.answer("Ошибка при создании базового билета.")

    await check_and_trigger_closure(message.bot)
