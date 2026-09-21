from db.db import (
    add_user, get_leaderboard, is_collection_closed, check_and_trigger_closure,
    get_user_applications, has_accepted_rules, mark_rules_accepted
)
import aiosqlite
from keyboards.menu import get_main_menu_keyboard, get_rules_agreement_keyboard
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)
    await check_and_trigger_closure(message.bot)

    if not await has_accepted_rules(user_id):
        agreement_text = (
            "Добро пожаловать в развлекательный квиз за 99 ₽ с розыгрышем iPhone 17!\n\n"
            "Для участия вам необходимо ознакомиться с правилами.\n\n"
            "«Я ознакомлен с <a href='https://cbda.ru/rules/base'>правилами розыгрыша</a> и согласен с их условиями, "
            "включая обработку моих данных (Telegram ID, username, результаты).»"
        )
        kb, progress = await get_main_menu_keyboard(user_id)
        await message.answer(
            agreement_text,
            reply_markup=get_rules_agreement_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        return

    kb, progress = await get_main_menu_keyboard(user_id)

    await message.answer(
        f"<b>Добро пожаловать в квиз за iPhone 17!</b>\n\n"
        "Каждая покупка за 99 ₽ даёт 1 базовый билет + возможность получить до +3 бонусных билетов в квизе!\n\n"
        f"{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "accept_rules")
async def accept_rules_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    await mark_rules_accepted(user_id)
    await callback.answer("✅ Правила приняты!")

    kb, progress = await get_main_menu_keyboard(user_id)
    await callback.message.answer(
        "<b>Спасибо! Теперь вы можете участвовать в розыгрыше.</b>\n\n"
        "Каждый платёж 99 ₽ даёт 1 базовый билет + возможность получить до +3 бонусных билетов за квиз!\n\n"
        f"{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    try:
        await callback.message.delete()
    except Exception:
        pass

@router.message(F.text == "📜 Правила розыгрыша")
@router.message(F.text == "❓ Правила конкурса")
async def cmd_rules(message: Message):
    rules_html = (
        "<b>📜 Правила розыгрыша iPhone 17</b>\n\n"
        "• Стоимость 1 попытки: <b>99 ₽</b>.\n"
        "• В каждую попытку входит:\n"
        "  — <b>1 гарантированный базовый билет</b>\n"
        "  — До <b>+3 бонусных билетов</b> за результат квиза (10 вопросов, 30 сек на вопрос):\n"
        "    • 10 правильных ответов: +3 бонусных билета\n"
        "    • 9 правильных ответов: +2 бонусных билета\n"
        "    • 8 правильных ответов: +1 бонусный билет\n"
        "    • Менее 8: без бонусов\n"
        "• Приём билетов останавливается при достижении <b>2500 билетов</b> или <b>10 апреля 2026</b>.\n"
        "• Розыгрыш iPhone 17 проводится среди всех выданных билетов с помощью https://www.random.org/ в прямом эфире в канале @mozgo_boy.\n\n"
        "Подробные условия: https://cbda.ru/rules/base"
    )
    await message.answer(rules_html, parse_mode="HTML", disable_web_page_preview=True)

@router.message(F.text == "🎟️ Мои билеты")
@router.message(F.text == "👤 Мои заявки")
async def cmd_my_tickets(message: Message):
    apps = await get_user_applications(message.from_user.id)

    if not apps:
        await message.answer("У вас пока нет билетов. Нажмите «🎁 Играть в Квиз за iPhone 17», чтобы получить первый билет!")
    else:
        text = "<b>🎟️ Ваши билеты:</b>\n\n"
        for t_num, status, score in apps:
            if status == "pending":
                st_str = "⏳ Ожидает квиза"
            elif status == "completed":
                st_str = "✅ Участвует в розыгрыше"
            else:
                st_str = "✅ Участвует в розыгрыше"

            score_str = f" (Квиз: {score}/10)" if score is not None else ""
            text += f"🎫 №{t_num:05d} — {st_str}{score_str}\n"

        await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
@router.message(F.text == "📊 Лидерборд")
@router.message(F.text == "📊 Лидерборд финалистов")
async def cmd_leaderboard(message: Message):
    leaders = await get_leaderboard(limit=20)
    if not leaders:
        await message.answer("Лидерборд пока пуст.")
        return

    text = "🏆 <b>Топ-20 участников по количеству билетов:</b>\n\n"
    for i, (username, full_name, t_count) in enumerate(leaders, 1):
        name = f"@{username}" if username else full_name
        text += f"{i}. {name} — <b>{t_count}</b> билетов\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
@router.message(F.text == "📞 Поддержка")
async def cmd_support(message: Message):
    await message.answer("По всем вопросам обращайтесь в поддержку бота по электронной почте alexandr@cbda.ru")

@router.message(F.text == "🔄 Обновить данные")
async def cmd_refresh(message: Message):
    user_id = message.from_user.id
    kb, progress = await get_main_menu_keyboard(user_id)
    await message.answer(f"🔄 Данные обновлены!\n\n{progress}", reply_markup=kb, parse_mode="HTML")
