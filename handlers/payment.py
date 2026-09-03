from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from db.db import add_user, issue_ticket, set_quiz_session, is_collection_closed, check_and_trigger_closure, log_payment
from keyboards.menu import get_start_quiz_keyboard
import config
import logging

payment_router = Router(name="payment_router")

@payment_router.message(F.text == "🆓 Бесплатная заявка на участие")
async def start_free_attempt(message: Message):
    user_id = message.from_user.id

    from db.db import has_accepted_rules
    if not await has_accepted_rules(user_id):
        await message.answer("Пожалуйста, примите правила конкурса в главном меню (/start) перед участием.")
        return

    if await is_collection_closed():
        await message.answer("🎉 Приём заявок завершён!")
        return

    from db.db import has_user_used_free_attempt
    if await has_user_used_free_attempt(user_id):
        await message.answer("Вы уже использовали свою бесплатную попытку.")
        return

    ticket_num = await issue_ticket(user_id, "base")
    if ticket_num:
        await set_quiz_session(user_id, ticket_num, score=0, current_question=0, is_active=True)
        warning_text = (
            f"✅ Ваша заявка №{ticket_num:05d} создана.\n\n"
            "⚠️ <b>Внимание!</b> Когда будете проходить квиз выбирайте время и место чтобы у вас был устойчивый интернет и входящие звонки не мешали прохождению квиза. "
            "При закрытии окна или выхода из приложения отсутствие ответов будет оцениваться как проигрыш.\n\n"
            "Готовы пройти квиз?"
        )
        await message.answer(warning_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании заявки.")

@payment_router.callback_query(F.data == "pay_99")
@payment_router.message(F.text == "💰 Поддержать (99 ₽)")
async def start_payment(event: Message | CallbackQuery):
    if isinstance(event, CallbackQuery):
        user_id = event.from_user.id
        bot = event.bot
        await event.answer()
    else:
        user_id = event.from_user.id
        bot = event.bot

    from db.db import has_accepted_rules
    if not await has_accepted_rules(user_id):
        msg = "Пожалуйста, примите правила в главном меню (/start) перед участием."
        if isinstance(event, CallbackQuery):
            await bot.send_message(user_id, msg)
        else:
            await event.answer(msg)
        return

    if await is_collection_closed():
        msg = (
            "🎉 Сбор билетов завершён досрочно!\n\n"
            "Мы набрали 2500+ билетов. Спасибо всем участникам!\n\n"
            "Розыгрыш iPhone 17 состоится в ближайшее время в прямом эфире в канале @mozgo_boy.\n\n"
            "Следи за обновлениями!"
        )
        if isinstance(event, CallbackQuery):
            await bot.send_message(user_id, msg)
        else:
            await event.answer(msg)
        return

    if isinstance(event, CallbackQuery):
        await bot.send_message(user_id, "🧾 Формируем счёт на 99 ₽...")
        try:
            await bot.send_invoice(
                chat_id=user_id,
                title="Квиз за iPhone 17",
                description="Оплата попытки в квизе за iPhone 17 (1 базовый билет + до +3 бонусных).",
                provider_token=config.YOOKASSA_PROVIDER_TOKEN,
                currency="RUB",
                prices=[LabeledPrice(label="Попытка в квизе", amount=9900)],
                payload="ticket_purchase"
            )
        except Exception as e:
            logging.error(f"Invoice error: {e}")
            await bot.send_message(user_id, f"❌ Ошибка: {e}")
    else:
        await event.answer("🧾 Формируем счёт на 99 ₽...")
        try:
            await event.answer_invoice(
                title="Квиз за iPhone 17",
                description="Оплата попытки в квизе за iPhone 17 (1 базовый билет + до +3 бонусных).",
                provider_token=config.YOOKASSA_PROVIDER_TOKEN,
                currency="RUB",
                prices=[LabeledPrice(label="Попытка в квизе", amount=9900)],
                payload="ticket_purchase"
            )
        except Exception as e:
            logging.error(f"Invoice error: {e}")
            await event.answer(f"❌ Ошибка: {e}")

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
        pay_text = (
            f"🎉 <b>Оплата прошла! Твой базовый билет №{ticket_num:05d} получен</b>\n\n"
            "Прямо сейчас ты можешь пройти квиз из 10 вопросов и получить до <b>+3 бонусных билетов</b>!\n\n"
            "⚠️ <b>Внимание!</b> На каждый вопрос даётся 30 секунд. Выбирай устойчивое интернет-соединение.\n\n"
            "Готов начать квиз?"
        )
        await message.answer(pay_text, reply_markup=get_start_quiz_keyboard(), parse_mode="HTML")
    else:
        await message.answer("Ошибка при создании билета.")

    await check_and_trigger_closure(message.bot)
