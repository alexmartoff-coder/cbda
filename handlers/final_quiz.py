from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from handlers.quiz_states import QuizStates
from database.db import (
    get_quiz_session, update_quiz_score, update_quiz_question, finish_quiz_session,
    check_and_trigger_closure, add_user, update_ticket_result, get_all_finalists,
    CHANNEL_ID
)
from keyboards.menu import get_main_menu_keyboard
from utils.generator import generate_questions
from database.db_final import is_final_active, get_final_times
import asyncio
import time
import logging
import html
import aiosqlite
from datetime import datetime, timedelta
from utils.time_utils import get_moscow_now

router = Router()

active_final_timers = {}

async def start_final_quiz_for_ticket(bot: Bot, user_id: int, ticket_number: int, q_count=8, is_mini=False, state: FSMContext = None):
    # Подбираем вопросы
    questions = await generate_questions(user_id, q_count)

    if state is None:
        # If no state provided, we don't have a reliable way to get it without circular imports in this structure
        # unless we pass it everywhere. For now, let's assume we pass it or get it via the bot if it had a reference.
        # But in aiogram 3, the Bot doesn't have a reference to the Dispatcher.
        # Let's use a workaround: we'll use a global variable in a separate module to store the DP.
        from utils.state_helper import get_state
        state = await get_state(bot, user_id)

    await state.update_data(
        final_questions=questions,
        current_ticket_num=ticket_number,
        final_score=0,
        final_start_time=time.time(),
        final_responses_time=0.0,
        is_mini_quiz=is_mini,
        q_count=q_count
    )
    await send_final_question(bot, state, user_id, 0)

async def send_final_question(bot: Bot, state: FSMContext, user_id: int, q_idx: int):
    if not await is_final_active():
        await bot.send_message(user_id, "⌛ Финал завершён.")
        await finish_all_final_sessions(bot, user_id)
        return

    data = await state.get_data()
    questions = data.get("final_questions")

    if not questions or q_idx >= len(questions):
        await finish_ticket_final(bot, state, user_id)
        return

    await state.set_state(QuizStates.answering) # Reusing state
    await state.update_data(current_final_q_idx=q_idx)

    question = questions[q_idx]

    prefix = "⚡️" if data.get("is_mini_quiz") else "🏁"

    if q_idx == 0:
        title = "⚡️ <b>МИНИ-КВИЗ</b>" if data.get("is_mini_quiz") else "🏁 <b>ФИНАЛЬНЫЙ КВИЗ</b>"
        header = f"{title} (Заявка №{data['current_ticket_num']:05d})\n\n"
    else:
        header = ""

    text = f"{header}{prefix} Вопрос {q_idx + 1}/{data['q_count']}\n\n{html.escape(question['question'])}\n\n⏱ У тебя 12 секунд!"

    keyboard = []
    for i, opt in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(text=opt, callback_data=f"fan_{q_idx}_{i}")])

    msg = await bot.send_message(user_id, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="HTML")

    await state.update_data(q_sent_at=time.time())

    timer = asyncio.create_task(final_timer(bot, state, user_id, q_idx, msg.message_id))
    active_final_timers[user_id] = timer

async def final_timer(bot: Bot, state: FSMContext, user_id: int, q_idx: int, msg_id: int):
    try:
        await asyncio.sleep(12)
        data = await state.get_data()
        if data.get("current_final_q_idx") == q_idx:
            await state.set_state(None)
            try: await bot.edit_message_reply_markup(user_id, msg_id, reply_markup=None)
            except: pass

            # В фоновом режиме: время вышло -> 0 баллов за вопрос
            await bot.send_message(user_id, "⏰ Время вышло!")
            # Добавляем максимальное время (12с) в общую копилку времени
            data = await state.get_data()
            await state.update_data(final_responses_time=data.get('final_responses_time', 0.0) + 12.0)
            await send_final_question(bot, state, user_id, q_idx + 1)
    except asyncio.CancelledError:
        pass
    finally:
        if user_id in active_final_timers:
            # We check if it's the same task to avoid removing a new timer
            if active_final_timers[user_id] == asyncio.current_task():
                active_final_timers.pop(user_id, None)

@router.callback_query(F.data.startswith("fan_"))
async def process_final_answer(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    q_idx_in_cb = int(callback.data.split("_")[1])
    ans_idx = int(callback.data.split("_")[2])

    if data.get("current_final_q_idx") != q_idx_in_cb: return

    if callback.from_user.id in active_final_timers:
        active_final_timers.pop(callback.from_user.id).cancel()

    resp_time = time.time() - data['q_sent_at']
    await state.update_data(final_responses_time=data['final_responses_time'] + resp_time)

    question = data['final_questions'][q_idx_in_cb]
    if ans_idx == question['correct_index']:
        await state.update_data(final_score=data['final_score'] + 1)

    await state.set_state(None)
    try: await callback.message.edit_reply_markup(reply_markup=None)
    except: pass

    await send_final_question(callback.bot, state, callback.from_user.id, q_idx_in_cb + 1)

async def finish_ticket_final(bot: Bot, state: FSMContext, user_id: int):
    data = await state.get_data()
    if not data: return # Already finished or cleared

    t_num = data.get('current_ticket_num')
    score = data.get('final_score', 0)
    resp_time = data.get('final_responses_time', 0.0)
    is_mini = data.get("is_mini_quiz", False)

    from database.db import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO final_results (ticket_number, user_id, score, total_time, finished_at, is_mini_quiz)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (t_num, user_id, score, resp_time, 1 if is_mini else 0))

        await db.execute("UPDATE final_sessions SET current_ticket_index = current_ticket_index + 1 WHERE user_id = ?", (user_id,))
        await db.commit()

    if is_mini:
        from database.db_winner import get_user_mini_quiz_tickets, get_mini_quiz_winner
        all_mini = await get_user_mini_quiz_tickets(user_id)
        if all_mini:
            next_t = all_mini[0]
            kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Начать квиз", callback_data=f"start_next_mini_{next_t}")]])
            await bot.send_message(user_id, f"✅ Мини-квиз для №{t_num:05d} завершён.\n\nСледующая ваша спорная заявка №{next_t:05d}.\nПерерыв 60 секунд или начните сейчас.", reply_markup=kb)

            await asyncio.sleep(60)
            session_data = await state.get_data()
            if session_data.get("current_ticket_num") == t_num:
                await start_final_quiz_for_ticket(bot, user_id, next_t, q_count=5, is_mini=True, state=state)
            return
        else:
            # Больше нет билетов в мини-квизе у этого юзера.
            # Если это был последний активный мини-квиз во всем боте, публикуем итоги.
            from database.db import DB_PATH
            async with aiosqlite.connect(DB_PATH) as db:
                # Находим количество незавершенных мини-квизов во всей системе
                query = """
                    SELECT COUNT(*) FROM tickets
                    WHERE ticket_number IN (
                        SELECT REPLACE(key, 'mini_quiz_pending_', '') FROM settings WHERE key LIKE 'mini_quiz_pending_%' AND value = '1'
                    )
                    AND ticket_number NOT IN (SELECT ticket_number FROM final_results WHERE is_mini_quiz = 1)
                """
                async with db.execute(query) as cursor:
                    remaining_global = (await cursor.fetchone())[0]

            if remaining_global == 0:
                from handlers.admin import publish_final_results
                await publish_final_results(bot)
            return

    from database.db_final import get_user_finalist_tickets
    all_tickets = await get_user_finalist_tickets(user_id)

    from database.db import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT current_ticket_index FROM final_sessions WHERE user_id = ?", (user_id,)) as c:
            next_idx = (await c.fetchone())[0]

    if next_idx < len(all_tickets):
        next_t = all_tickets[next_idx]
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Начать квиз", callback_data=f"start_next_final_{next_t}")]])
        await bot.send_message(user_id, f"✅ Квиз для заявки №{t_num:05d} завершён.\nРезультат: <b>{score}/8</b>\n\nСледующая ваша заявка №{next_t:05d}.\nПерерыв 60 секунд или начните сейчас.", reply_markup=kb, parse_mode="HTML")

        # Таймер на 60 сек (в фоне, чтобы не блокировать хендлер)
        async def wait_and_start():
            await asyncio.sleep(60)
            try:
                current_data = await state.get_data()
                if current_data.get("current_ticket_num") == t_num:
                    await start_final_quiz_for_ticket(bot, user_id, next_t, state=state)
            except: pass
        asyncio.create_task(wait_and_start())
    else:
        await bot.send_message(user_id, f"✅ Квиз для заявки №{t_num:05d} завершён.\nРезультат: <b>{score}/8</b>\n\n🎉 Поздравляем! Вы прошли Финал для всех своих заявок ({len(all_tickets)} шт.).\nРезультаты будут подведены в ближайшее время.", parse_mode="HTML")
        from database.db import DB_PATH
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE final_sessions SET is_active = 0 WHERE user_id = ?", (user_id,))
            await db.commit()
        await state.clear()

        # Проверяем, не был ли это ПОСЛЕДНИЙ активный билет во всем финале
        async with aiosqlite.connect(DB_PATH) as db:
            # Считаем количество активных сессий
            async with db.execute("SELECT COUNT(*) FROM final_sessions WHERE is_active = 1") as cursor:
                active_sessions = (await cursor.fetchone())[0]

        if active_sessions == 0:
            # Все зарегистрированные закончили.
            from database.db_final import get_final_times, get_final_stats
            times = await get_final_times()
            if times:
                stats = await get_final_stats()
                now = get_moscow_now().replace(tzinfo=None)

                # Условия для ранней публикации:
                # 1. Регистрация закрыта (19:30+)
                # 2. ИЛИ Все финалисты уже зарегистрировались (X == Y)
                # 3. ИЛИ это тестовый режим
                all_registered = stats['registered_tickets'] >= stats['total_finalist_tickets']

                if now >= times["reg_end"] or all_registered or times.get("is_test"):
                    from handlers.admin import publish_final_results
                    await publish_final_results(bot)

@router.callback_query(F.data.startswith("start_next_final_"))
async def start_next_final_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    next_t = int(callback.data.split("_")[-1])
    try: await callback.message.edit_reply_markup(reply_markup=None)
    except: pass
    await start_final_quiz_for_ticket(callback.bot, callback.from_user.id, next_t, state=state)

@router.callback_query(F.data.startswith("start_next_mini_"))
async def start_next_mini_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    next_t = int(callback.data.split("_")[-1])
    try: await callback.message.edit_reply_markup(reply_markup=None)
    except: pass
    await start_final_quiz_for_ticket(callback.bot, callback.from_user.id, next_t, q_count=5, is_mini=True, state=state)

async def start_schedulers(bot: Bot):
    sent_pushes = set() # To avoid duplicate pushes in the same loop
    last_test_start = None

    while True:
        try:
            from database.db_final import get_final_times
            times = await get_final_times()
            if times:
                now = get_moscow_now().replace(tzinfo=None)
                day_key = now.strftime("%Y-%m-%d")

                # Сброс пушей при смене тестового времени
                current_test_start = times.get("reg_start").isoformat() if times.get("is_test") else "prod"
                if last_test_start != current_test_start:
                    sent_pushes.clear()
                    last_test_start = current_test_start

                # Пуш о начале регистрации (reg_start)
                push_key = f"reg_start_{day_key}_{times['reg_start'].strftime('%H:%M:%S')}"
                if now >= times["reg_start"] and push_key not in sent_pushes:
                    finalists = await get_all_finalists()
                    for fid in finalists:
                        try:
                            kb, _ = await get_main_menu_keyboard(fid)
                            remaining = times["reg_end"] - get_moscow_now().replace(tzinfo=None)
                            rem_str = str(remaining).split(".")[0]
                            msg = f"🔔 <b>Началась регистрация на финал.</b> Завершение регистрации в 19:30 Мск. Не опаздывайте.\n⏳ До закрытия: <b>{rem_str}</b>"
                            await bot.send_message(fid, msg, parse_mode="HTML", reply_markup=kb)
                            await asyncio.sleep(0.05) # Rate limiting
                        except: pass
                    sent_pushes.add(push_key)

                # Пуш о завершении финала и расчет итогов (final_end)
                push_key_end = f"final_end_complete_{day_key}_{times['final_end'].strftime('%H:%M:%S')}"
                if now >= times["final_end"] and push_key_end not in sent_pushes:
                    # Вызываем единую функцию публикации, которая обработает и Ничью, и Победителя
                    from handlers.admin import publish_final_results
                    await publish_final_results(bot)
                    sent_pushes.add(push_key_end)

                # Пуш об аннулировании (reg_end)
                push_key_cancel = f"reg_end_{day_key}_{times['reg_end'].strftime('%H:%M:%S')}"
                if now >= times["reg_end"] and push_key_cancel not in sent_pushes:
                    # Находим всех, кто не зарегистрировался
                    from database.db_final import has_user_registered_for_final
                    finalists = await get_all_finalists()
                    for fid in finalists:
                        if not await has_user_registered_for_final(fid):
                            try:
                                await bot.send_message(fid, "⌛ <b>Регистрация завершена.</b>\n\nВы не успели войти в Финал, ваши заявки аннулированы.")
                                await asyncio.sleep(0.05) # Rate limiting
                            except: pass
                    sent_pushes.add(push_key_cancel)

                # Пуш о начале мини-квиза (через 30 мин после final_end)
                mini_start = times["final_end"] + timedelta(minutes=30)
                push_key_mini = f"mini_start_{day_key}_{mini_start.strftime('%H:%M:%S')}"
                if now >= mini_start and push_key_mini not in sent_pushes:
                    from database.db_winner import check_for_ties
                    ties = await check_for_ties()
                    if ties:
                        unique_users = list(set([t[1] for t in ties]))
                        for uid in unique_users:
                            try:
                                # Проверяем, не начал ли он уже мини-квиз
                                from database.db_winner import get_user_mini_quiz_tickets
                                if await get_user_mini_quiz_tickets(uid):
                                    kb, _ = await get_main_menu_keyboard(uid)
                                    await bot.send_message(uid, "🔔 <b>Начало МИНИ-КВИЗА!</b>\n\nИспользуйте кнопку в меню.", parse_mode="HTML", reply_markup=kb)
                                    await asyncio.sleep(0.05) # Rate limiting
                            except: pass
                    sent_pushes.add(push_key_mini)

        except Exception as e:
            logging.error(f"Scheduler error: {e}")
        await asyncio.sleep(10)

async def finish_all_final_sessions(bot: Bot, user_id: int):
    # Log logic for 21:00 cutoff
    pass
