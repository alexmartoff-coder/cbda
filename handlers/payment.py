from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton
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

    mechanics_text = (
        "🤖 <b>Правила квиза «iPhone 17»</b>\n\n"
        "Каждый платёж в размере <b>99 ₽</b> даёт:\n"
        "1. 🎟️ <b>1 гарантированный базовый билет</b> на участие в розыгрыше.\n"
        "2. 🧠 <b>Возможность получить бонусные билеты</b> за отличные знания в квизе:\n"
        "   • 🏆 10 правильных ответов → <b>+3 бонусных билета</b>\n"
        "   • 🥈 9 правильных ответов → <b>+2 бонусных билета</b>\n"
        "   • 🥉 8 правильных ответов → <b>+1 бонусный билет</b>\n"
        "   • ❌ Меньше 8 правильных ответов → бонусные билеты не начисляются.\n\n"
        "Квиз состоит из 10 вопросов на тему Apple. Время на ответ — 30 секунд на один вопрос.\n\n"
        "Готовы попытать удачу? Нажмите кнопку ниже для оплаты!"
    )

    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])
    await message.answer(mechanics_text, reply_markup=inline_kb, parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not await has_accepted_rules(user_id):
        await callback.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.", show_alert=True)
        return

    if await is_collection_closed():
        await callback.answer("🎉 Приём билетов завершён!", show_alert=True)
        return

    await callback.answer()
    await callback.message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        await callback.message.answer_invoice(
            title="Участие в квизе за iPhone 17",
            description="Базовый билет + участие в квизе с возможностью получить до +3 бонусных билетов.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Поддержка", amount=9900)],
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

    ticket_num = await issue_ticket(user_id, "base", status="pending")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        warning_text = (
            f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз, выбирайте время и место, чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выходе из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Готовы начать квиз?"
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета.")

    await check_and_trigger_closure(message.bot)
