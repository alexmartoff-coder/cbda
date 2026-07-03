from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard, get_payment_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def play_quiz_start(message: Message):
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

    mechanics_text = (
        "<b>Как получить билеты:</b>\n\n"
        "1. Оплати 99 ₽ — ты сразу получишь <b>1 гарантированный базовый билет</b>.\n"
        "2. Пройди квиз из 10 вопросов об Apple.\n"
        "3. Получи дополнительные бонусные билеты за результат:\n"
        "   ✅ 10 правильных ответов — <b>+3 бонусных билета</b>\n"
        "   ✅ 9 правильных ответов — <b>+2 бонусных билета</b>\n"
        "   ✅ 8 правильных ответов — <b>+1 бонусный билет</b>\n\n"
        "Все полученные билеты участвуют в розыгрыше iPhone 17!"
    )
    await message.answer(mechanics_text, reply_markup=get_payment_keyboard(), parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    await callback.answer()

    if await is_collection_closed():
        await callback.message.answer("🎉 Приём заявок завершён!")
        return

    try:
        await callback.message.answer_invoice(
            title="Билет на квиз iPhone 17",
            description="1 базовый билет + до 3 бонусных за квиз.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка при формировании счета. Попробуйте позже.")

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

    ticket_num = await issue_ticket(user_id, "base", status='pending')
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        success_text = (
            f"✅ Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "⚠️ <b>Внимание!</b> Выбирай время и место с устойчивым интернетом. "
            "При закрытии окна или выходе из приложения квиз прервется.\n\n"
            "Готов начать квиз?"
        )
        await message.answer(success_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета. Пожалуйста, обратитесь в поддержку.")

    await check_and_trigger_closure(message.bot)
