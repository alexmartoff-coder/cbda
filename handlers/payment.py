from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🎁 Играть в Квиз за iPhone 17")
async def play_button_handler(message: Message):
    from db.db import has_accepted_rules
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

    description = (
        "<b>Участвуй в розыгрыше iPhone 17!</b>\n\n"
        "💳 Стоимость участия: <b>99 ₽</b>\n\n"
        "🎁 Что ты получаешь:\n"
        "1️⃣ <b>1 гарантированный базовый билет</b> сразу после оплаты.\n"
        "2️⃣ <b>Возможность получить до +3 бонусных билетов</b>, ответив правильно на вопросы квиза:\n"
        "   • 10 правильных ответов — <b>+3 билета</b>\n"
        "   • 9 правильных ответов — <b>+2 билета</b>\n"
        "   • 8 правильных ответов — <b>+1 билет</b>\n\n"
        "Чем больше билетов, тем выше шансы на победу! 🚀"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])

    await message.answer(description, reply_markup=kb, parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def process_pay_99_callback(callback: CallbackQuery):
    await callback.answer()

    if await is_collection_closed():
        await callback.message.answer("🎉 Приём билетов завершён!")
        return

    try:
        await callback.message.answer_invoice(
            title="Билет на квиз iPhone 17",
            description="1 базовый билет + бонусные за квиз.",
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

    ticket_num = await issue_ticket(user_id, "base", status='completed')
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        success_text = (
            f"✅ <b>Оплата прошла!</b>\n\n"
            f"Твой базовый билет <b>№{ticket_num:05d}</b> получен.\n\n"
            "Теперь давай заработаем бонусные билеты в квизе! 🚀\n\n"
            "⚠️ <b>Внимание!</b> Выбирай время и место, чтобы интернет был стабильным. "
            "Если выйдешь из квиза, перепройти его будет нельзя."
        )
        await message.answer(success_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета. Обратитесь в поддержку.")

    await check_and_trigger_closure(message.bot)
