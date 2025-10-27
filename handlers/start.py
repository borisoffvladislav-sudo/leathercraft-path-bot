from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    print("🎯 /start из start.py")
    await message.answer("✅ Start команда работает!")

@router.message(Command("profile"))
async def profile_cmd(message: types.Message):
    print("🎯 /profile из start.py")
    await message.answer("✅ Profile команда работает!")