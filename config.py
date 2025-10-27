import os
from dotenv import load_dotenv

load_dotenv()

# Настройки бота
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = None

# Пути к картинкам
IMAGE_MAP = {
    "welcome": "images/start/welcome.jpg",
    "worker": "images/new_character/worker.jpg", 
    "manager": "images/new_character/manager.jpg",
    "blogger": "images/new_character/blogger.jpg",
    "confirm": "images/confirmation/confirm.jpg",
    "info_character": "images/info_character/info.jpg",
    "profile": "images/info_character/info.jpg",
    "placeholder": "images/placeholder.jpg"
}