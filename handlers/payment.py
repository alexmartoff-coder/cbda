from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from database.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard, get_payment_keyboard
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
        await message.answer("🎉 Приём заявок завершён!")
        return

    description = (
        "🎮 <b>Как это работает?</b>\n\n"
        "1. Вы оплачиваете участие (99 ₽).\n"
        "2. Получаете 1 гарантированный билет.\n"
        "3. Проходите квиз из 10 вопросов об Apple.\n"
        "4. Получаете бонусные билеты за правильные ответы:\n"
        "   ✅ 10 верных — <b>+3 билета</b>\n"
        "   ✅ 9 верных — <b>+2 билета</b>\n"
        "   ✅ 8 верных — <b>+1 билет</b>\n\n"
        "Больше билетов — выше шансы на победу!"
    )

    await message.answer(description, reply_markup=get_payment_keyboard(), parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    if await is_collection_closed():
        await callback.answer("🎉 Приём заявок завершён!", show_alert=True)
        return

    await callback.message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        await callback.message.answer_invoice(
            title="Участие в квизе + билеты",
            description="1 базовый билет + сессия квиза для получения бонусов.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие", amount=9900)],
            payload="quiz_entry"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await callback.message.answer(f"❌ Ошибка: {e}")

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
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        warning_text = (
            f"✅ Оплата прошла успешно! Ваша базовая заявка №{ticket_num:05d} создана.\n\n"
            "⚠️ <b>Внимание!</b> Сейчас начнется квиз для получения бонусных билетов. "
            "Выбирайте время и место, чтобы у вас был устойчивый интернет и входящие звонки не мешали. "
            "При закрытии окна или выходе из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Готовы?"
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании заявки. Обратитесь в поддержку.")

    await check_and_trigger_closure(message.bot)
