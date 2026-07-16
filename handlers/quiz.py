from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from handlers.quiz_states import QuizStates
from db.db import get_quiz_session, update_quiz_score, update_quiz_question, finish_quiz_session, check_and_trigger_closure, add_user, update_ticket_result, issue_ticket
from keyboards.menu import get_main_menu_keyboard, get_start_quiz_keyboard
from utils.generator import generate_questions
import asyncio
import time
import logging
from config import TICKET_LIMIT, CHANNEL_ID
import html
import aiosqlite

router = Router()

active_quiz_timers = {}

def build_keyboard(question, q_idx):
    keyboard = []
    for i, option in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(
            text=option,
            callback_data=f"qans_{question['id']}_{i}_{q_idx}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def safe_send_question(bot: Bot, state: FSMContext, user_id: int, q_idx: int):
    current_task = asyncio.current_task()
    if user_id in active_quiz_timers:
        old_task = active_quiz_timers[user_id]
        if old_task != current_task:
            old_task.cancel()
        active_quiz_timers.pop(user_id, None)

    data = await state.get_data()
    questions = data.get("current_questions")

    if not questions or q_idx >= len(questions):
        await finish_quiz_logic(bot, state, user_id)
        return

    await state.set_state(QuizStates.answering)
    await state.update_data(current_question_index=q_idx)

    question = questions[q_idx]
    q_text = html.escape(question['question'])
    text = f"❓ <b>Вопрос {q_idx + 1}/10</b>\n\n{q_text}\n\n⏱ У тебя 30 секунд!"

    try:
        msg = await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=build_keyboard(question, q_idx),
            parse_mode="HTML"
        )

        await state.update_data(
            question_msg_id=msg.message_id,
            start_time=time.time()
        )

        timer_task = asyncio.create_task(quiz_timer_logic(bot, state, user_id, q_idx, msg.message_id))
        active_quiz_timers[user_id] = timer_task

    except Exception as e:
        logging.error(f"Error: {e}")

async def quiz_timer_logic(bot: Bot, state: FSMContext, user_id: int, q_idx: int, msg_id: int):
    try:
        await asyncio.sleep(30)
        data = await state.get_data()
        current_state = await state.get_state()

        if current_state == QuizStates.answering and data.get("current_question_index") == q_idx:
            await state.set_state(None)
            try: await bot.edit_message_reply_markup(chat_id=user_id, message_id=msg_id, reply_markup=None)
            except: pass

            questions = data.get("current_questions")
            question = questions[q_idx]
            correct_text = html.escape(question['options'][question['correct_index']])
            expl_text = html.escape(question['explanation'])

            await bot.send_message(
                chat_id=user_id,
                text=f"⏰ <b>Время вышло!</b>\n\n❌ Правильный ответ: <b>{correct_text}</b>\n\n{expl_text}",
                parse_mode="HTML"
            )

            next_idx = q_idx + 1
            await update_quiz_question(user_id, next_idx)
            await asyncio.sleep(3)
            await safe_send_question(bot, state, user_id, next_idx)
    except asyncio.CancelledError: pass
    finally:
        if active_quiz_timers.get(user_id) == asyncio.current_task():
            active_quiz_timers.pop(user_id, None)

@router.callback_query(F.data == "start_quiz")
async def start_quiz_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    session = await get_quiz_session(user_id)

    if not session or not session[2]:
        await callback.message.answer("У вас нет активной заявки!")
        return

    loading = await callback.message.answer("🔄 Подбираем вопросы...")

    try:
        from db.db import mark_questions_as_seen
        questions = await generate_questions(user_id, 10)
        await state.update_data(current_questions=questions)
        seen_ids = [q["pool_index"] for q in questions]
        await mark_questions_as_seen(user_id, seen_ids)

        try: await loading.delete()
        except: pass
        await safe_send_question(callback.bot, state, user_id, 0)
    except Exception as e:
        logging.error(f"Error: {e}")

@router.callback_query(QuizStates.answering, F.data.startswith("qans_"))
async def process_quiz_answer(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    data = await state.get_data()

    try:
        parts = callback.data.split("_")
        ans_idx = int(parts[2])
        q_idx_in_cb = int(parts[3])
    except: return

    if q_idx_in_cb != data.get("current_question_index"): return

    if user_id in active_quiz_timers:
        task = active_quiz_timers.pop(user_id)
        if not task.done(): task.cancel()

    await state.set_state(None)
    try: await callback.message.edit_reply_markup(reply_markup=None)
    except: pass

    questions = data.get("current_questions")
    question = questions[q_idx_in_cb]
    is_correct = ans_idx == question['correct_index']
    correct_text = html.escape(question['options'][question['correct_index']])
    expl_text = html.escape(question['explanation'])

    if is_correct:
        session = await get_quiz_session(user_id)
        new_score = (session[0] if session else 0) + 1
        await update_quiz_score(user_id, new_score)
        res_text = f"✅ <b>Верно!</b>\n\n{expl_text}"
    else:
        res_text = f"❌ <b>Неверно.</b> Правильный ответ: <b>{correct_text}</b>\n\n{expl_text}"

    await callback.message.answer(res_text, parse_mode="HTML")
    await update_quiz_question(user_id, q_idx_in_cb + 1)
    await asyncio.sleep(3)
    await safe_send_question(callback.bot, state, user_id, q_idx_in_cb + 1)

async def finish_quiz_logic(bot: Bot, state: FSMContext, user_id: int):
    if user_id in active_quiz_timers:
        task = active_quiz_timers.pop(user_id)
        if not task.done(): task.cancel()

    session = await get_quiz_session(user_id)
    score = session[0] if session else 0
    t_num = session[3] if session else None

    bonus_tickets = 0
    if score == 10:
        bonus_tickets = 3
    elif score == 9:
        bonus_tickets = 2
    elif score == 8:
        bonus_tickets = 1

    bonus_ticket_nums = []
    for _ in range(bonus_tickets):
        bn = await issue_ticket(user_id, "bonus", status='completed')
        if bn:
            bonus_ticket_nums.append(bn)

    await update_ticket_result(t_num, 'completed', score)
    await finish_quiz_session(user_id)
    await state.clear()

    bonus_text = ""
    if bonus_tickets > 0:
        nums_str = ", ".join([f"№{n:05d}" for n in bonus_ticket_nums])
        bonus_text = f"\n\n🔥 <b>Потрясающе!</b> Ты получаешь {bonus_tickets} бонусных билета: {nums_str}"
    elif score >= 8: # This should not happen with logic above but for safety
        bonus_text = f"\n\nТы получил бонусные билеты за отличный результат!"
    else:
        bonus_text = "\n\nБонусных билетов в этот раз нет, но твой базовый билет участвует в розыгрыше!"

    final_msg = (
        f"🏁 <b>Квиз завершён!</b>\n"
        f"Твой результат: <b>{score}/10</b>"
        f"{bonus_text}\n\n"
        f"Общее количество билетов за эту попытку: <b>{1 + len(bonus_ticket_nums)}</b>"
    )

    kb, progress = await get_main_menu_keyboard(user_id)
    await bot.send_message(
        chat_id=user_id,
        text=f"{final_msg}\n\n{progress}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await check_and_trigger_closure(bot)
