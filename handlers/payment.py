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
        await message.answer(
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        return

    mechanics_text = (
        "<b>🎁 Развлекательный квиз за iPhone 17!</b>\n\n"
        "Каждый платёж (99 ₽) даёт:\n"
        "🎫 <b>1 гарантированный базовый билет</b>\n"
        "➕ Возможность получить до <b>+3 бонусных билетов</b> за правильные ответы в квизе:\n"
        "• 10 правильных ответов → <b>+3 бонусных билета</b>\n"
        "• 9 правильных ответов → <b>+2 бонусных билета</b>\n"
        "• 8 правильных ответов → <b>+1 бонусный билет</b>\n"
        "• Меньше 8 правильных ответов → без бонусов.\n\n"
        "Хотите принять участие?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить 99 ₽", callback_data="pay_99")]
    ])
    await message.answer(mechanics_text, reply_markup=kb, parse_mode="HTML")

@payment_router.callback_query(F.data == "pay_99")
async def start_payment(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not await has_accepted_rules(user_id):
        await callback.answer("Пожалуйста, примите правила в меню!", show_alert=True)
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
            title="Оплата участия в квизе за iPhone 17",
            description="Оплата 99 ₽ за участие и получение билетов в розыгрыше iPhone 17.",
            provider_token=config.YOOKASSA_PROVIDER_TOKEN,
            currency="RUB",
            prices=[LabeledPrice(label="Оплата", amount=9900)],
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
        await set_quiz_session(user_id, ticket_num, score=0, current_question=1, is_active=True)

        await message.answer(f"Оплата прошла! Твой базовый билет №{ticket_num:05d} получен")

        warning_text = (
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Готовы пройти квиз?"
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании платной заявки.")

    await check_and_trigger_closure(message.bot)
