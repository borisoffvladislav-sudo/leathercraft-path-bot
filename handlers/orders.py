from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("orders"))
async def orders_cmd(message: types.Message):
    print("🎯 /orders из orders.py")
    await message.answer("✅ Orders команда работает!")

@router.message(Command("work"))
async def work_cmd(message: types.Message):
    print("🎯 /work из orders.py")
    await message.answer("✅ Work команда работает!")
    