import random
import logging
from data.questions_pool import QUESTIONS_POOL

from db.db import get_user_seen_question_ids, clear_user_seen_questions

async def generate_questions(user_id, amount=10):
    # === FIXED: РАНДОМИЗАЦИЯ КВИЗА И ЗАЩИТА ОТ ПОВТОРОВ ===
    seen_ids = await get_user_seen_question_ids(user_id)

    # Отфильтровываем вопросы, которые пользователь уже видел
    # Используем индекс в списке QUESTIONS_POOL как ID для простоты
    available_questions = [
        (idx, q) for idx, q in enumerate(QUESTIONS_POOL)
        if idx not in seen_ids
    ]

    # Если доступных вопросов меньше 10, сбрасываем историю (пул пройден)
    if len(available_questions) < amount:
        logging.info(f"User {user_id} saw most questions. Resetting pool.")
        await clear_user_seen_questions(user_id)
        available_questions = [(idx, q) for idx, q in enumerate(QUESTIONS_POOL)]

    logging.info(f"Selecting {amount} random questions for {user_id} from {len(available_questions)} available")

    selected_indices_and_qs = random.sample(available_questions, min(amount, len(available_questions)))

    final_questions = []
    prefix = ["A. ", "B. ", "C. ", "D. "]

    for q_idx, q in selected_indices_and_qs:
        # Создаем копию вопроса
        q_copy = q.copy()
        q_copy["pool_index"] = q_idx # Сохраняем индекс для БД

        # Перемешиваем варианты ответов
        options = q_copy["options"].copy()
        correct_option = options[q_copy["correct_index"]]
        random.shuffle(options)

        # Обновляем правильный индекс после перемешивания
        q_copy["correct_index"] = options.index(correct_option)

        # Добавляем буквы A, B, C, D к вариантам
        formatted_options = []
        for i, opt in enumerate(options):
            formatted_options.append(f"{prefix[i]}{opt}")

        q_copy["options"] = formatted_options

        # Добавляем уникальный ID
        q_copy["id"] = random.randint(1000, 9999)

        final_questions.append(q_copy)

    return final_questions
