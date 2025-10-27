# bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # ПРАВИЛЬНЫЙ ПОРЯДОК ПОДКЛЮЧЕНИЯ РОУТЕРОВ
    # Сначала подключаем start_router - он обрабатывает /start и основные кнопки
    from routers.start import start_router
    dp.include_router(start_router)
    
    # Затем tutorial_router - он обрабатывает обучение
    from routers.tutorial import tutorial_router
    dp.include_router(tutorial_router)
    
    # И только потом другие роутеры
    from routers.orders import orders_router
    dp.include_router(orders_router)
    
    print("✅ Все роутеры подключены в правильном порядке")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())