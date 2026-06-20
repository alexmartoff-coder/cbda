import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from db.db import init_db
from handlers import base, quiz, admin, payment, final_quiz

# Логирование
logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация БД
    await init_db()

    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    from utils.state_helper import set_dp
    set_dp(dp)

    # Запуск планировщика задач
    from handlers.final_quiz import start_schedulers
    asyncio.create_task(start_schedulers(bot))

    # Регистрируем роутеры
    dp.include_router(payment.payment_router)
    dp.include_router(admin.router)
    dp.include_router(final_quiz.router)
    dp.include_router(base.router)
    dp.include_router(quiz.router)

    logging.info("Starting @googlestop_bot...")

    # Сброс вебхуков
    await bot.delete_webhook(drop_pending_updates=True)

    # Автоматически определяем необходимые типы обновлений
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
