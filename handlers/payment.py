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

    # If the contest is closed, the bot answers with the specific closure notification
    if await is_collection_closed():
        closure_text = (
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        await message.answer(closure_text)
        return

    # Clicking the menu button displays a description of the mechanics followed by an inline 'Оплатить 99 ₽' button to initiate the transaction.
    mechanics_text = (
        "🧠 <b>Развлекательный квиз за iPhone 17!</b>\n\n"
        "Каждое участие стоит <b>99 ₽</b> и даёт:\n"
        "• <b>1 гарантированный базовый билет</b> на розыгрыш.\n"
        "• Возможность получить <b>до +3 бонусных билетов</b> за правильные ответы в квизе!\n\n"
        "<b>Бонусные билеты начисляются так:</b>\n"
        "🏆 <b>10 правильных ответов</b> → +3 бонусных билета\n"
        "🥈 <b>9 правильных ответов</b> → +2 бонусных билета\n"
        "🥉 <b>8 правильных ответов</b> → +1 бонусный билет\n"
        "❌ Меньше 8 правильных → бонусов нет.\n\n"
        "У тебя есть 10 вопросов и 30 секунд на размышление по каждому вопросу.\n\n"
        "Нажми кнопку ниже, чтобы оплатить и начать игру!"
    )

    pay_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])

    await message.answer(mechanics_text, reply_markup=pay_keyboard, parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await has_accepted_rules(user_id):
        await callback.answer("Пожалуйста, примите правила конкурса!", show_alert=True)
        return

    if await is_collection_closed():
        await callback.message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        await callback.answer()
        return

    await callback.message.answer("🧾 Формируем счёт на 99 RUB...")
    await callback.answer()

    try:
        await callback.message.answer_invoice(
            title="Квиз за iPhone 17",
            description="Оплата участия в квизе + 1 гарантированный базовый билет",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Оплата участия", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка формирования счета: {e}")

@payment_router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    # Mandatory PreCheckoutQuery handler to approve incoming transaction requests
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
        warning_text = (
            f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Готовы пройти квиз?"
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета.")

    await check_and_trigger_closure(message.bot)
