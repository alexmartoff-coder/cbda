from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard, get_payment_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def show_mechanics(message: Message):
    from db.db import has_accepted_rules
    if not await has_accepted_rules(message.from_user.id):
        await message.answer("Пожалуйста, примите правила розыгрыша в главном меню (/start) перед участием.")
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
        "<b>Как работает розыгрыш iPhone 17:</b>\n\n"
        "1. Ты оплачиваешь 99 ₽.\n"
        "2. Получаешь 1 гарантированный базовый билет.\n"
        "3. Проходишь квиз из 10 вопросов об Apple.\n"
        "4. За хорошие результаты начисляются <b>бонусные билеты</b>:\n"
        "   ✅ 10 правильных ответов — <b>+3 билета</b>\n"
        "   ✅ 9 правильных ответов — <b>+2 билета</b>\n"
        "   ✅ 8 правильных ответов — <b>+1 билет</b>\n\n"
        "Чем больше билетов, тем выше шанс на победу!"
    )
    await message.answer(mechanics_text, reply_markup=get_payment_keyboard(), parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    await callback.answer()
    message = callback.message

    if await is_collection_closed():
        await message.answer("🎉 Сбор билетов завершён!")
        return

    try:
        await message.answer_invoice(
            title="Участие в розыгрыше iPhone 17",
            description="1 базовый билет + до 3 бонусных за квиз.",
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
        await message.answer(f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.")

        warning_text = (
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Готовы начать квиз?"
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Произошла ошибка при выдаче билета. Пожалуйста, обратитесь в поддержку.")

    await check_and_trigger_closure(message.bot)
