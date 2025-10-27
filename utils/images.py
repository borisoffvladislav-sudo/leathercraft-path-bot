import os
from aiogram.types import FSInputFile
from config import IMAGE_MAP

async def send_photo_safe(bot, chat_id, key, caption="", reply_markup=None):
    rel_path = IMAGE_MAP.get(key, "images/placeholder.jpg")
    abs_path = os.path.join(os.path.dirname(__file__), "..", rel_path)

    if not os.path.exists(abs_path):
        abs_path = os.path.join(os.path.dirname(__file__), "..", "images/placeholder.jpg")
        if not os.path.exists(abs_path):
            print(f"[ERROR] Placeholder не найден по пути {abs_path}")
            await bot.send_message(chat_id, caption, reply_markup=reply_markup)
            return

    try:
        await bot.send_photo(chat_id, photo=FSInputFile(abs_path), caption=caption, reply_markup=reply_markup)
    except Exception as e:
        print(f"[ERROR] Не удалось отправить фото {abs_path}: {e}")
        await bot.send_message(chat_id, caption, reply_markup=reply_markup)