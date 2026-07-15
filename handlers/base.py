from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from db.db import add_user, mark_rules_accepted, has_accepted_rules, get_user_applications, get_leaderboard, is_collection_closed, get_total_tickets_count
from keyboards.menu import get_main_menu_keyboard, get_rules_agreement_keyboard
from config import OWNER_ID

router = Router(name="base_router")

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user = message.from_user
    await add_user(user_id, user.username, user.full_name)

    rules_accepted = await has_accepted_rules(user_id)
    kb, progress = await get_main_menu_keyboard(user_id)

    if not rules_accepted:
        welcome_text = (
            "👋 Привет! Добро пожаловать в квиз-розыгрыш iPhone 17!\n\n"
            "Чтобы продолжить, пожалуйста, ознакомьтесь с правилами конкурса."
        )
        await message.answer(welcome_text, reply_markup=get_rules_agreement_keyboard())
    else:
        await message.answer(f"{progress}\n\nВыбери действие в меню:", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "accept_rules")
async def process_accept_rules(callback: CallbackQuery):
    user_id = callback.from_user.id
    await mark_rules_accepted(user_id)
    await callback.answer("Правила приняты!")

    kb, progress = await get_main_menu_keyboard(user_id)
    await callback.message.answer(
        f"✅ Спасибо за принятие правил!\n\n{progress}\n\nТеперь вы можете участвовать в розыгрыше.",
        reply_markup=kb,
        parse_mode="HTML"
    )
    try: await callback.message.delete()
    except: pass

@router.message(F.text == "📜 Правила розыгрыша")
@router.message(Command("rules"))
async def cmd_rules(message: Message):
    rules_text = (
        "📜 <b>Правила розыгрыша iPhone 17:</b>\n\n"
        "1. Стоимость участия — 99 ₽.\n"
        "2. Каждый платёж даёт 1 базовый билет.\n"
        "3. После оплаты вы проходите квиз из 10 вопросов.\n"
        "4. Бонусные билеты за квиз:\n"
        "   — 10 правильных: +3 билета\n"
        "   — 9 правильных: +2 билета\n"
        "   — 8 правильных: +1 билет\n"
        "5. Сбор билетов завершается при достижении 2500 билетов или 10 апреля 2026.\n"
        "6. Победитель выбирается случайным образом с помощью random.org среди всех выданных билетов.\n"
        "7. Розыгрыш пройдёт в прямом эфире в канале @mozgo_boy."
    )
    await message.answer(rules_text, parse_mode="HTML")

@router.message(F.text == "🎟️ Мои билеты")
@router.message(Command("my_tickets"))
async def cmd_my_tickets(message: Message):
    user_id = message.from_user.id
    tickets = await get_user_applications(user_id)

    if not tickets:
        await message.answer("У вас пока нет билетов. Нажмите «🎁 Играть», чтобы участвовать!")
        return

    tickets_list = "\n".join([f"🎟️ Билет №{t[0]:05d} ({t[1]})" for t in tickets])
    await message.answer(f"<b>Ваши билеты:</b>\n\n{tickets_list}", parse_mode="HTML")

@router.message(F.text == "🏆 Лидерборд")
@router.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message):
    leaderboard = await get_leaderboard()
    if not leaderboard:
        await message.answer("Лидерборд пока пуст.")
        return

    text = "🏆 <b>Топ участников по количеству билетов:</b>\n\n"
    for i, (username, full_name, count) in enumerate(leaderboard, 1):
        name = username or full_name or "Аноним"
        text += f"{i}. {name} — {count} 🎟️\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❓ Поддержка")
@router.message(Command("support"))
async def cmd_support(message: Message):
    await message.answer("По всем вопросам пишите на почту: alexandr@cbda.ru")

@router.message(F.text == "🔄 Обновить данные")
async def cmd_refresh(message: Message):
    user_id = message.from_user.id
    kb, progress = await get_main_menu_keyboard(user_id)
    await message.answer(progress, reply_markup=kb, parse_mode="HTML")
