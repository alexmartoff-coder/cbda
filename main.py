import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from db.db import init_db
from handlers import base, quiz, admin, payment
from db.db import check_and_trigger_closure

# Логирование
logging.basicConfig(level=logging.INFO)

async def scheduler(bot: Bot):
    while True:
        try:
            await check_and_trigger_closure(bot)
        except Exception as e:
            logging.error(f"Scheduler error: {e}")
        await asyncio.sleep(3600) # Check every hour

async def main():
    # Инициализация БД
    await init_db()

    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    from utils.state_helper import set_dp
    set_dp(dp)

    # Запуск планировщика
    asyncio.create_task(scheduler(bot))

    # Регистрируем роутеры
    dp.include_router(payment.payment_router)
    dp.include_router(admin.router)
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
