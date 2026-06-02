from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import OWNER_ID
from database.db_admin import get_all_users_data
from database.db import DB_PATH
from keyboards.menu import get_admin_keyboard, get_db_download_keyboard, get_main_menu_keyboard
from utils.google_sheets import export_to_google_sheets
import os
import aiosqlite
import asyncio
import random
from datetime import datetime, timedelta

router = Router()

@router.message(Command("admin"))
@router.message(F.text == "👨‍💼 Админ-панель")
async def cmd_admin(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    await message.answer("🛠 <b>Панель администратора</b>",
                         reply_markup=get_admin_keyboard(),
                         parse_mode="HTML")

@router.message(F.text == "📊 Экспорт в Google Sheets")
async def admin_export_google(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    status_msg = await message.answer("⏳ Подготовка данных и выгрузка в Google Sheets...")

    data = await get_all_users_data()
    url, error = await export_to_google_sheets(data)

    if error:
        await status_msg.edit_text(f"❌ Ошибка при экспорте:\n{error}")
    else:
        await status_msg.edit_text(f"✅ Данные успешно выгружены!\n\n🔗 <a href='{url}'>Открыть Google Таблицу</a>",
                                  parse_mode="HTML",
                                  disable_web_page_preview=False)

@router.message(F.text == "🏁 Управление Финалом")
async def admin_final_management(message: Message):
    if message.from_user.id != OWNER_ID: return
    from database.db_final import get_final_stats
    stats = await get_final_stats()
    text = (
        f"🏁 <b>Управление Финалом</b>\n\n"
        f"Всего финалистов (заявок): {stats['total_finalist_tickets']}\n"
        f"Зарегистрировалось: {stats['registered_tickets']} (юзеров: {stats['registered_users']})\n"
        f"Завершили прохождение: {stats['finished_tickets']}\n"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Рассчитать итоги", callback_data="admin_calc_final")],
        [InlineKeyboardButton(text="🚀 Тест: Регистрация СЕЙЧАС", callback_data="admin_test_reg_now")],
        [InlineKeyboardButton(text="🏁 Тест: Финал СЕЙЧАС", callback_data="admin_test_final_now")],
        [InlineKeyboardButton(text="⏰ Тест: Завершить Финал", callback_data="admin_test_finish_now")],
        [InlineKeyboardButton(text="❌ Сброс тестов", callback_data="admin_test_reset")],
        [InlineKeyboardButton(text="🛠 Сид тестовых данных (3495)", callback_data="admin_seed_data")],
        [InlineKeyboardButton(text="🛠 Сид тестовых данных (741)", callback_data="admin_seed_data_741")]
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "admin_calc_final")
async def admin_calc_final(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from database.db_winner import get_preliminary_winner, check_for_ties
    winner = await get_preliminary_winner()
    ties = await check_for_ties()

    if not winner:
        await callback.message.answer("Результатов финала пока нет.")
    elif ties:
        await callback.message.answer(f"⚠️ <b>Выявлено равенство результатов!</b>\nНужен мини-квиз для {len(ties)} заявок.", parse_mode="HTML")
    else:
        # Победитель определен
        from database.db import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT username, full_name FROM users WHERE user_id = ?", (winner[1],)) as c:
                u = await c.fetchone()
                name = u[0] if u[0] else u[1]

        text = (
            f"🏆 <b>Победитель определён!</b>\n\n"
            f"Участник: {name} (@{u[0]})\n"
            f"Заявка: №{winner[0]:05d}\n"
            f"Результат: {winner[2]}/8\n"
            f"Время: {winner[3]:.2f} сек."
        )
        await callback.message.answer(text, parse_mode="HTML")

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Опубликовать итоги в канал", callback_data="admin_publish_results")]
        ])
        await callback.message.answer("Опубликовать результаты?", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data == "admin_seed_data")
async def admin_seed_data_handler(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from tests.seed_test_data import seed_data
    await seed_data(3495)
    await callback.message.answer("✅ База данных засеяна (3495 заявок)!")
    await callback.answer()

@router.callback_query(F.data == "admin_seed_data_741")
async def admin_seed_data_741_handler(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from tests.seed_test_data import seed_data
    await seed_data(741)
    await callback.message.answer("✅ База данных засеяна (741 заявка)!")
    await callback.answer()

@router.callback_query(F.data == "admin_test_reg_now")
async def admin_test_reg_now(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from utils.time_utils import get_moscow_now
    now = get_moscow_now().replace(tzinfo=None)
    test_start = now - timedelta(minutes=1) # Already running for 1 min
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('test_reg_start', ?)", (test_start.isoformat(),))
        await db.commit()

    # Trigger push through scheduler logic manually to ensure it's marked
    from handlers.final_quiz import sent_pushes
    day_key = now.strftime("%Y-%m-%d")
    push_key = f"reg_start_{day_key}_{test_start.strftime('%H:%M:%S')}"
    sent_pushes.add(push_key)

    from database.db import get_all_finalists
    from database.db_final import get_final_times
    from keyboards.menu import get_main_menu_keyboard

    finalists = await get_all_finalists()
    times = await get_final_times()
    for fid in finalists:
        try:
            kb, _ = await get_main_menu_keyboard(fid)
            remaining = times["reg_end"] - get_moscow_now().replace(tzinfo=None)
            rem_str = str(remaining).split(".")[0]
            msg = f"🔔 <b>Началась регистрация на финал.</b> Завершение регистрации в 19:30 Мск. Не опаздывайте.\n⏳ До закрытия: <b>{rem_str}</b>"
            await callback.bot.send_message(fid, msg, parse_mode="HTML", reply_markup=kb)
        except: pass

    await callback.message.answer("🚀 <b>Тест: Регистрация запущена и уведомления разосланы!</b>\nПроверьте главное меню.", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_test_final_now")
async def admin_test_final_now(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from utils.time_utils import get_moscow_now
    now = get_moscow_now().replace(tzinfo=None)
    test_start = now - timedelta(minutes=31) # Регистрация закончилась 1 мин назад
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('test_reg_start', ?)", (test_start.isoformat(),))
        await db.commit()
    await callback.message.answer("🏁 <b>Тест: Финал запущен!</b>\nПроверьте главное меню.", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_test_finish_now")
async def admin_test_finish_now(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    from utils.time_utils import get_moscow_now
    now = get_moscow_now().replace(tzinfo=None)
    test_start = now - timedelta(hours=2, minutes=1) # Финал закончился 1 мин назад
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('test_reg_start', ?)", (test_start.isoformat(),))
        await db.commit()

    # Сразу публикуем результаты
    await publish_final_results(callback.bot)

    await callback.message.answer("⏰ <b>Тест: Финал завершен и итоги опубликованы!</b>", parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_test_reset")
async def admin_test_reset(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM settings WHERE key = 'test_reg_start'")
        await db.commit()
    await callback.message.answer("❌ Тестовые настройки сброшены.")
    await callback.answer()

async def publish_final_results(bot: Bot):
    from database.db_winner import get_preliminary_winner, get_mini_quiz_winner, check_for_ties, setup_mini_quiz
    from database.db_final import get_final_stats, get_final_times
    from database.db import DB_PATH, CHANNEL_ID
    import aiosqlite
    import random
    from utils.time_utils import get_moscow_now

    times = await get_final_times()
    if not times: return
    now = get_moscow_now().replace(tzinfo=None)

    # Проверяем условия для публикации:
    # 1. Регистрация закрыта (19:30+)
    # 2. ИЛИ Все финалисты уже зарегистрировались
    # 3. ИЛИ это тестовый режим
    stats = await get_final_stats()
    all_registered = stats['registered_tickets'] >= stats['total_finalist_tickets']

    if not (now >= times["reg_end"] or all_registered or times.get("is_test")):
        return

    # 1. Проверяем, не опубликованы ли уже результаты
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = 'results_published'") as c:
            if await c.fetchone(): return

    # 2. Получаем статистику
    stats = await get_final_stats()
    y = stats['total_finalist_tickets']
    x = stats['registered_tickets']
    z = y - x
    k = stats['finished_tickets']
    l = x - k

    # 3. Ищем победителя (сначала мини-квиз)
    winner = await get_mini_quiz_winner()

    if not winner:
        # Проверяем на ничью
        ties = await check_for_ties()
        if ties:
            # Проверяем, не объявляли ли мы уже о ничьей
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute("SELECT value FROM settings WHERE key = 'tie_broadcasted'") as c:
                    if not await c.fetchone():
                        public_text = (
                            "🎉 <b>Финал завершён!</b>\n\n"
                            f"Всего финалистских заявок: {y}\n"
                            f"Зарегистрировалось (нажали кнопку): {x}\n"
                            f"Не зарегистрировалось (не нажали до 19:30): {z} = {y} – {x}\n"
                            f"Успешно прошли финал (полностью или частично): {k}\n"
                            f"Не завершили прохождение (не уложились в 21:00): {l}\n\n"
                            "⚠️ <b>Выявлено равенство результатов!</b>\n"
                            f"Для {len(ties)} заявок будет проведён дополнительный мини-квиз в 21:30 МСК."
                        )
                        try: await bot.send_message(CHANNEL_ID, public_text, parse_mode="HTML")
                        except: pass

                        await setup_mini_quiz(bot, ties)
                        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('tie_broadcasted', '1')", ())
                        await db.commit()
            return
        else:
            winner = await get_preliminary_winner()

    if not winner: return

    # 4. Победитель определён - публикуем!
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT username, full_name FROM users WHERE user_id = ?", (winner[1],)) as c:
            u = await c.fetchone()
            username = "@" + u[0] if (u and u[0]) else (u[1] if u else "Участник")

        win_code = "".join([str(random.randint(0,9)) for _ in range(6)])
        await db.execute("INSERT OR REPLACE INTO winners (user_id, ticket_number, code) VALUES (?, ?, ?)",
                         (winner[1], winner[0], win_code))
        await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('results_published', '1')", ())
        await db.commit()

    minutes, seconds = int(winner[3] // 60), int(winner[3] % 60)
    time_str = f"{minutes:02d}:{seconds:02d}"

    public_text = (
        "🎉 <b>Финал завершён!</b>\n\n"
        f"Всего финалистских заявок: {y}\n"
        f"Зарегистрировалось (нажали кнопку): {x}\n"
        f"Не зарегистрировалось (не нажали до 19:30): {z} = {y} – {x}\n"
        f"Успешно прошли финал (полностью или частично): {k}\n"
        f"Не завершили прохождение (не уложились в 21:00): {l}\n\n"
        "🏆 <b>Победитель конкурса определён!</b>\n"
        f"Победитель: {username} (заявка №{winner[0]:05d})\n"
        f"Результат: {winner[2]}/8, время {time_str}\n"
        f"Приз: iPhone 17 PRO 256 Гб\n\n"
        "Поздравляем победителя!\n"
        "Приз (iPhone 17 PRO 256 Гб) будет вручён только после подтверждения секретного кода. "
        "Код отправлен победителю в личные сообщения."
    )

    try: await bot.send_message(CHANNEL_ID, public_text, parse_mode="HTML")
    except: pass

    # Рассылка всем
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            all_users = await cursor.fetchall()
            for (uid,) in all_users:
                try:
                    from keyboards.menu import get_main_menu_keyboard
                    kb, _ = await get_main_menu_keyboard(uid)
                    await bot.send_message(uid, public_text, parse_mode="HTML", reply_markup=kb)
                    await asyncio.sleep(0.05)
                except: pass

    win_msg = (
        "Ваш приз: <b>iPhone 17 PRO 256 Гб</b>\n\n"
        f"🔑 Ваш секретный код: <code>{win_code}</code>\n\n"
        "⚠️ <b>Важная информация:</b>\n"
        "• Никому не сообщайте этот код. Даже если кто-то пишет вам от имени организатора.\n"
        "• Для получения приза напишите организатору в личные сообщения на почту alexandr@cbda.ru\n"
        f"Обязательно укажите свой секретный код: {win_code}"
    )
    try: await bot.send_message(winner[1], win_msg, parse_mode="HTML")
    except: pass

    from utils.time_utils import get_moscow_now
    gen_date = get_moscow_now().strftime("%d.%m.%Y %H:%M")
    admin_msg = (
        f"Победитель: {username}\n"
        f"Заявка №{winner[0]:05d}\n"
        f"Результат: {winner[2]}/8 | Время: {time_str}\n"
        f"Секретный код: {win_code}\n"
        f"Дата генерации: {gen_date}"
    )
    try: await bot.send_message(OWNER_ID, f"✅ <b>Результаты опубликованы!</b>\n\n{admin_msg}", parse_mode="HTML")
    except: pass

@router.callback_query(F.data == "admin_publish_results")
async def admin_publish_results_handler(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID: return
    await publish_final_results(callback.bot)
    await callback.answer()

@router.message(F.text == "🏆 Победитель")
async def admin_winner(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT w.user_id, w.ticket_number, w.code, w.won_at,
                   fr.score, fr.total_time, u.username, u.full_name
            FROM winners w
            JOIN final_results fr ON w.ticket_number = fr.ticket_number
            JOIN users u ON w.user_id = u.user_id
            LIMIT 1
        """
        async with db.execute(query) as cursor:
            winner = await cursor.fetchone()

    if not winner:
        await message.answer("ℹ️ Победитель ещё не определён.\nДля полной выгрузки используйте кнопку ниже.",
                             reply_markup=get_db_download_keyboard())
        return

    uid, t_num, code, won_at, score, total_time, username, full_name = winner

    name = f"@{username}" if username else full_name
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    time_str = f"{minutes:02d}:{seconds:02d}"

    # Форматирование даты из БД (Current_timestamp обычно YYYY-MM-DD HH:MM:SS)
    try:
        dt = datetime.fromisoformat(won_at.replace(" ", "T"))
        date_str = dt.strftime("%d.%m.%Y %H:%M")
    except:
        date_str = won_at

    text = (
        f"🏆 <b>Информация о победителе</b>\n\n"
        f"Победитель: {name}\n"
        f"Заявка №{t_num:05d}\n"
        f"Результат: {score}/8 | Время: {time_str}\n"
        f"Секретный код: <code>{code}</code>\n"
        f"Дата генерации: {date_str}"
    )

    await message.answer(text, reply_markup=get_db_download_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "download_db")
async def download_db(callback: CallbackQuery):
    if callback.from_user.id != OWNER_ID:
        await callback.answer("Доступ запрещен", show_alert=True)
        return

    if os.path.exists(DB_PATH):
        await callback.message.answer_document(FSInputFile(DB_PATH), caption="📂 Актуальная база данных (SQLite)")
    else:
        await callback.answer("Файл базы данных не найден", show_alert=True)

    await callback.answer()

@router.message(F.text == "🔙 Назад в главное меню")
async def back_to_main(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    kb, progress = await get_main_menu_keyboard(message.from_user.id)
    await message.answer(f"{progress}\n\nПереходим в главное меню...", reply_markup=kb)
