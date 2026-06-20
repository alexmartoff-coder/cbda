from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from database.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard, get_pay_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def start_quiz_flow(message: Message):
    user_id = message.from_user.id

    from database.db import has_accepted_rules
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

    description = (
        "<b>Как получить iPhone 17 за 99 ₽?</b>\n\n"
        "1. Оплатите участие (99 ₽).\n"
        "2. Получите 1 гарантированный базовый билет.\n"
        "3. Пройдите квиз из 10 вопросов.\n"
        "4. Получите бонусные билеты за верные ответы:\n"
        "   ✅ 10 правильных → +3 билета\n"
        "   ✅ 9 правильных → +2 билета\n"
        "   ✅ 8 правильных → +1 билет\n\n"
        "Больше билетов — выше шансы на победу!"
    )
    await message.answer(description, reply_markup=get_pay_keyboard(), parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def process_pay_99(callback: CallbackQuery):
    await callback.answer()
    if await is_collection_closed():
        await callback.message.answer("🎉 Сбор билетов завершён!")
        return

    try:
        await callback.message.answer_invoice(
            title="Билет + Квиз за iPhone 17",
            description="Оплата участия в розыгрыше iPhone 17.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка при формировании счета: {e}")

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
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        text = (
            f"✅ Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Нажмите кнопку ниже, чтобы начать квиз и получить бонусные билеты!"
        )
        await message.answer(text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета. Обратитесь в поддержку.")

    await check_and_trigger_closure(message.bot)
