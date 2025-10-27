# routers/orders.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

orders_router = Router()

# Заглушка для теста
@orders_router.message(Command("orders"))
async def orders_command(message: Message):
    await message.answer("Команда /orders работает! Система заказов в разработке.")