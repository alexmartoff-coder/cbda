from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def start_quiz_flow(message: Message):
    from db.db import has_accepted_rules
    if not await has_accepted_rules(message.from_user.id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        text = (
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        await message.answer(text)
        return

    text = (
        "<b>🎁 Участвуй в розыгрыше iPhone 17!</b>\n\n"
        "Правила просты:\n"
        "1. Оплати участие (99 ₽).\n"
        "2. Получи 1 гарантированный базовый билет.\n"
        "3. Пройди квиз из 10 вопросов и получи до +3 бонусных билетов!\n\n"
        "<b>Бонусы за квиз:</b>\n"
        "✅ 10 правильных — +3 билета\n"
        "✅ 9 правильных — +2 билета\n"
        "✅ 8 правильных — +1 билет\n\n"
        "Больше билетов — выше шанс на победу!"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])

    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def process_pay_99(callback: CallbackQuery):
    await callback.answer()
    message = callback.message

    if await is_collection_closed():
        text = (
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        await message.answer(text)
        return

    await message.answer("🧾 Формируем счёт на 99 RUB...")

    try:
        await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title="Билет + Квиз (iPhone 17)",
            description="1 базовый билет + возможность получить до +3 бонусных билетов в квизе.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Участие", amount=9900)],
            payload="ticket_purchase"
        )
    except Exception as e:
        logging.error(f"Invoice error: {e}")
        await message.answer(f"❌ Ошибка: {e}")

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
        success_text = (
            f"✅ Оплата прошла! Твой базовый билет №{ticket_num:05d} получен.\n\n"
            "Теперь давай получим бонусные билеты! Пройди квиз и покажи лучший результат.\n\n"
            "⚠️ <b>Внимание!</b> Выбирай время и место, чтобы интернет был устойчивым и звонки не отвлекали. "
            "Отсутствие ответа или закрытие приложения будет засчитано как неверный ответ.\n\n"
            "Готов начать?"
        )
        await message.answer(success_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета. Пожалуйста, обратитесь в поддержку.")

    await check_and_trigger_closure(message.bot)
