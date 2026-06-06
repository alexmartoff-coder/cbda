from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def start_payment_flow(message: Message):
    from database.db import has_accepted_rules
    if not await has_accepted_rules(message.from_user.id):
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

    mechanics_text = (
        "<b>Механика игры:</b>\n\n"
        "1. Оплати участие (99 ₽).\n"
        "2. Получи 1 гарантированный базовый билет.\n"
        "3. Пройди квиз из 10 вопросов и получи до +3 бонусных билетов за правильные ответы:\n"
        "   • 10 верных — +3 билета\n"
        "   • 9 верных — +2 билета\n"
        "   • 8 верных — +1 билет\n\n"
        "Больше билетов — выше шанс на победу!"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить 99 ₽", callback_data="pay_99")]
    ])

    await message.answer(mechanics_text, reply_markup=kb, parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def process_pay_99(callback: CallbackQuery):
    await callback.answer()

    if await is_collection_closed():
        await callback.message.answer("🎉 Приём заявок завершён!")
        return

    try:
        await callback.message.answer_invoice(
            title="Билет на квиз iPhone 17",
            description="1 базовый билет + участие в квизе за бонусы.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие", amount=9900)],
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

    ticket_num = await issue_ticket(user_id, "paid")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        warning_text = (
            f"✅ Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Готовы начать квиз?"
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета.")

    await check_and_trigger_closure(message.bot)
