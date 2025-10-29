# routers/start.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.models import Database
from routers.tutorial import get_showcase_keyboard
from routers.tutorial import (
    get_tutorial_start_keyboard, 
    get_approach_keyboard,
    get_oldman_approach_keyboard, 
    get_shop_menu_keyboard,
    TutorialStates, 
    
)
import os
import asyncio 

start_router = Router()
db = Database()

# Глобальная задержка для всех сообщений (в секундах)
MESSAGE_DELAY = 0.5

async def delayed_send(bot, chat_id, method, *args, **kwargs):
    """Универсальная функция для отправки сообщений с задержкой"""
    await asyncio.sleep(MESSAGE_DELAY)
    return await getattr(bot, method)(chat_id, *args, **kwargs)

# Состояния для регистрации
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_gender = State()  # ← ДОБАВЛЕНО состояние выбора пола
    choosing_class = State()
    confirming_class = State()
    final_confirmation = State()

# Состояния для управления персонажами
class PlayerManagementStates(StatesGroup):
    confirming_deletion = State()
    viewing_profile = State()

# Клавиатура для нового пользователя
def get_registration_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎭 Зарегистрироваться и создать персонажа", callback_data="start_registration")]
    ])
    return keyboard

# Клавиатура для пользователя с существующими персонажами
def get_existing_players_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Продолжить играть", callback_data="continue_playing")],
        [InlineKeyboardButton(text="➕ Создать нового", callback_data="create_new_character")],
        [InlineKeyboardButton(text="👤 Посмотреть профиль персонажа", callback_data="view_profile")]
    ])
    return keyboard

# Клавиатура для выбора пола 
def get_gender_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨 Мужской", callback_data="gender_male")],
        [InlineKeyboardButton(text="👩 Женский", callback_data="gender_female")]
    ])
    return keyboard

# Клавиатура для выбора класса
def get_classes_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠️ Работяга", callback_data="class_worker")],
        [InlineKeyboardButton(text="💼 Менеджер", callback_data="class_manager")],
        [InlineKeyboardButton(text="📱 Блоггер", callback_data="class_blogger")]
    ])
    return keyboard

# Клавиатура для подтверждения выбора класса
def get_class_confirmation_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выбрать этот класс", callback_data="confirm_class")],
        [InlineKeyboardButton(text="↩️ Назад к выбору", callback_data="back_to_classes")]
    ])
    return keyboard

# Клавиатура для финального подтверждения
def get_final_confirmation_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, подтверждаю выбор", callback_data="final_confirm")],
        [InlineKeyboardButton(text="↩️ Вернуться к классам", callback_data="back_to_class_info")]
    ])
    return keyboard

# Клавиатура для подтверждения удаления
def get_deletion_confirmation_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Да, удалить персонажа", callback_data="confirm_deletion")],
        [InlineKeyboardButton(text="↩️ Нет, оставить", callback_data="cancel_deletion")]
    ])
    return keyboard

# Клавиатура для ФИНАЛЬНОГО подтверждения удаления
def get_final_deletion_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить навсегда", callback_data="final_confirm_deletion")],
        [InlineKeyboardButton(text="↩️ Нет, я передумал", callback_data="cancel_final_deletion")]
    ])
    return keyboard

# Клавиатура для профиля персонажа
def get_profile_management_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Продолжить играть", callback_data="continue_playing")],
        [InlineKeyboardButton(text="🗑️ Удалить персонажа", callback_data="delete_character")]
    ])
    return keyboard

# Клавиатура основного меню игры
def get_main_menu_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠️ Работа", callback_data="work_menu")],
        [InlineKeyboardButton(text="📋 Заказы", callback_data="orders_menu")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="view_profile")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")]
    ])
    return keyboard

@start_router.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Добавляем/получаем пользователя в БД
    db.add_user(user_id, username, first_name, message.from_user.last_name)
    
    # Проверяем есть ли у пользователя активные персонажи
    active_players = db.get_user_players(user_id)
    
    # Пытаемся отправить картинку
    image_path = "images/welcome.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        if active_players:
            # Уже есть персонажи - предлагаем выбор
            await message.answer_photo(
                photo=photo,
                caption=f"👋 С возвращением, {first_name}!\n\n"
                       "У тебя уже есть созданные персонажи. Что хочешь сделать?",
                reply_markup=get_existing_players_keyboard()
            )
        else:
            # Новый пользователь - предлагаем регистрацию
            await message.answer_photo(
                photo=photo,
                caption="👋 Добро пожаловать в 'Путь кожевника'!\n\n"
                       "Здесь ты сможешь освоить ремесло кожевника, "
                       "создавать уникальные изделия и строить свою мастерскую!\n\n"
                       "🎯 Для начала создай своего первого персонажа!",
                reply_markup=get_registration_keyboard()
            )
    except Exception as e:
        # Если картинка не отправляется, все равно отправляем текст
        if active_players:
            await message.answer(
                f"👋 С возвращением, {first_name}!\n\n"
                "У тебя уже есть созданные персонажи. Что хочешь сделать?",
                reply_markup=get_existing_players_keyboard()
            )
        else:
            await message.answer(
                "👋 Добро пожаловать в 'Путь кожевника'!\n\n"
                "🎯 Для начала создай своего первого персонажа!",
                reply_markup=get_registration_keyboard()
            )

# Обработка кнопки "Зарегистрироваться"
@start_router.callback_query(F.data == "start_registration")
async def start_registration(callback: CallbackQuery, state: FSMContext):
    # Удаляем кнопки из предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Задержка перед следующим сообщением
    await asyncio.sleep(MESSAGE_DELAY)
    
    # Пытаемся отправить картинку
    image_path = "images/create_character.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption="🎭 Давай создадим твоего персонажа!\n\n"
                   "Как зовут твоего будущего кожевника?\n"
                   "(Выбери уникальное имя от 2 до 20 символов)",
        )
    except Exception as e:
        await callback.message.answer(
            "🎭 Давай создадим твоего персонажа!\n\n"
            "Как зовут твоего будущего кожевника?\n"
            "(Выбери уникальное имя от 2 до 20 символов)",
        )
    
    await state.set_state(RegistrationStates.waiting_for_name)
    await callback.answer()

# Обработка ввода имени
@start_router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    
    # Проверяем длину имени
    if len(name) < 2 or len(name) > 20:
        # Задержка перед сообщением об ошибке
        await asyncio.sleep(MESSAGE_DELAY)
        
        # Отправляем сообщение с картинкой об ошибке
        image_path = "images/error.jpg"
        if not os.path.exists(image_path):
            image_path = "images/placeholder.jpg"
        
        try:
            photo = FSInputFile(image_path)
            await message.answer_photo(
                photo=photo,
                caption="❌ Имя должно быть от 2 до 20 символов. Попробуй еще раз:"
            )
        except:
            await message.answer("❌ Имя должно быть от 2 до 20 символов. Попробуй еще раз:")
        return
    
    # ВРЕМЕННО УБИРАЕМ ПРОВЕРКУ УНИКАЛЬНОСТИ ИМЕНИ
    # TODO: Добавить метод is_player_name_taken в Database
    
    # Сохраняем имя в состоянии
    await state.update_data(character_name=name)
    
    # Задержка перед выбором пола
    await asyncio.sleep(MESSAGE_DELAY)
    
    # Пытаемся отправить картинку выбора пола ← ИЗМЕНЕНО: было выбор класса, стало выбор пола
    image_path = "images/gender_selection.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await message.answer_photo(
            photo=photo,
            caption="🎯 Отлично! Теперь выбери пол персонажа:",
            reply_markup=get_gender_keyboard()
        )
    except Exception as e:
        await message.answer(
            "🎯 Отлично! Теперь выбери пол персонажа:",
            reply_markup=get_gender_keyboard()
        )
    
    await state.set_state(RegistrationStates.waiting_for_gender)  # ← ИЗМЕНЕНО: было choosing_class

# Обработка выбора пола
@start_router.callback_query(F.data.startswith("gender_"), RegistrationStates.waiting_for_gender)
async def process_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split("_")[1]  # "male" или "female"
    
    await state.update_data(player_gender=gender)
    
    # Удаляем сообщение с выбором пола
    try:
        await callback.message.delete()
    except:
        pass  # Игнорируем если не удалось удалить
    
    # Задержка перед выбором класса
    await asyncio.sleep(MESSAGE_DELAY)
    
    # Переходим к выбору класса с картинкой
    image_path = "images/classes.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption="🎯 Отлично! Теперь выбери класс персонажа:\n\n"
                   "🛠️ **Работяга** - мастер на все руки\n"
                   "💼 **Менеджер** - специалист по продажам\n"
                   "📱 **Блоггер** - разорившийся инфлюенсер с фанатами",
            reply_markup=get_classes_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            "🎯 Отлично! Теперь выбери класс персонажа:\n\n"
            "🛠️ **Работяга** - мастер на все руки\n"
            "💼 **Менеджер** - специалист по продажам\n"
            "📱 **Блоггер** - разорившийся инфлюенсер с фанатами",
            reply_markup=get_classes_keyboard()
        )
    
    await state.set_state(RegistrationStates.choosing_class)
    await callback.answer()

# Обработка кнопки "Начать играть" - ПЕРЕМЕЩЕН ИЗ TUTORIAL.PY
@start_router.callback_query(F.data == "start_tutorial")
async def start_tutorial_handler(callback: CallbackQuery, state: FSMContext):
    """Запускает обучение для нового игрока"""
    user_id = callback.from_user.id
    
    # Получаем активного персонажа
    active_player = db.get_active_player(user_id)
    if not active_player:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    player_id = active_player[0]  # ID персонажа
    player_name = active_player[2]  # имя персонажа
    player_class = active_player[3]  # класс персонажа
    
    # Инициализируем прогресс обучения для этого персонажа
    tutorial_db.init_tutorial_progress(player_id)
    tutorial_db.init_shop_items()
    
    # Определяем предысторию по классу
    if player_class == "Работяга":
        backstory = f"Вы пол жизни трудитесь на заводе. Работа не легкая, но честная. Каждый день, как часы, с 8:00 до 17:00 вы у станка. А после смены остается время на себя. Посмотреть сериал, погулять по городу с семьей, встретиться с друзьями. Обычная спокойная жизнь.\n\nОднажды вечером, листая ленту YouTube, вы наткнулись на видео, где мастер из куска кожи делал ремешок, а потом кошелек, а потом сумку. Так ловко и просто. Вам захотелось тоже попробовать сделать себе ремень. А если получится, то и сумку.\n\nВзяв часть накоплений, вы отправились в ближайший магазин, где продавали натуральную кожу."
        image_name = "worker_backstory.jpg"
    
    elif player_class == "Менеджер":
        backstory = f"Вы были обычным офисным работником, чьи дни проходили в бесконечных совещаниях и работе с таблицами. Вы чувствовали, как тонете в корпоративной рутине, где ваша инициатива никому не нужна, а реальные результаты работы размыты и абстрактны. Мир, состоящий из цифр и отчетов, казался вам пустым и лишенным смысла.\n\nДля отдыха вы смотрели YouTube, и однажды он подсунул вам канал кожевника. Ловко и просто мастер делал разные вещи. И что вам понравилось, результат своих трудов мастер мог подержать в руках, а что еще лучше – пользоваться им каждый день! Тогда вы решил попробовать и самостоятельно, что-то сделать у себя на кухне.\n\nВзяв часть накоплений, вы отправились в ближайший магазин, где продавали кожу."
        image_name = "manager_backstory.jpg"
    
    else:  # Блоггер
        backstory = f"Вы когда-то были известным блогером с тысячами подписчиков, строя свою жизнь на лайках и одобрении аудитории. Однако неудачное вложение в стартап обернулся финансовым крахом и блокировкой всех ваших соцсетей. В одночасье вы потеряли всё, что считали своей жизнью, осознав шаткость мира, построенного на чужих оценках.\n\nВ поисках нового пути вы обнаружили на YouTube сообщество мастеров-ремесленников. Их кропотливая работа с кожей, создание классных вещей, поразила вас. Это был шанс начать всё с чистого листа и построить не виртуальный, а реальный, осязаемый бизнес.\n\nВзяв часть накоплений, вы отправились в ближайший магазин, где продавали кожу."
        image_name = "blogger_backstory.jpg"
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        print(f"⚠️ Не удалось удалить кнопки: {e}")
        # Продолжаем выполнение даже если не удалось удалить кнопки
    
    # Пытаемся отправить картинку предыстории
    image_path = f"images/tutorial/{image_name}"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=backstory,
            reply_markup=get_tutorial_start_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            backstory,
            reply_markup=get_tutorial_start_keyboard()
        )
    
    await state.set_state(TutorialStates.waiting_for_shop_enter)
    await state.update_data(player_id=player_id)
    await callback.answer()

# Обработка выбора класса
@start_router.callback_query(F.data.startswith("class_"))
async def choose_class(callback: CallbackQuery, state: FSMContext):
    class_type = callback.data.replace("class_", "")
    
    # Определяем название класса и описание
    if class_type == "worker":
        class_name = "Работяга"
        description = "🛠️ **Работяга** - настоящий мастер своего дела!\n\n"
        description += "📊 **Стартовые характеристики:**\n"
        description += "• Мастерство: 25 (высокое)\n"
        description += "• Удача: 15 (средняя)\n" 
        description += "• Маркетинг: 5 (низкий)\n"
        description += "• Репутация: 5 (низкая)\n\n"
        description += "Идеально для тех, кто любит работать руками!"
        image_name = "worker_class.jpg"
        
    elif class_type == "manager":
        class_name = "Менеджер" 
        description = "💼 **Менеджер** - прирожденный продавец!\n\n"
        description += "📊 **Стартовые характеристики:**\n"
        description += "• Мастерство: 10 (низкое)\n"
        description += "• Удача: 15 (средняя)\n"
        description += "• Маркетинг: 25 (высокий)\n"
        description += "• Репутация: 10 (низкая)\n\n"
        description += "Отлично подходит для торговли и переговоров!"
        image_name = "manager_class.jpg"
        
    else:  # blogger
        class_name = "Блоггер"
        description = "📱 **Блоггер** - разорившийся инфлюенсер с фанатами!\n\n"
        description += "📊 **Стартовые характеристики:**\n"
        description += "• Мастерство: 5 (низкое)\n"
        description += "• Удача: 25 (высокая)\n"
        description += "• Маркетинг: 20 (высокий)\n"
        description += "• Репутация: 20 (высокая)\n\n"
        description += "Прекрасный выбор для создания бренда!"
        image_name = "blogger_class.jpg"
    
    # Сохраняем выбранный класс в состоянии
    await state.update_data(character_class=class_name, class_type=class_type)
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass  # Игнорируем ошибку если не можем изменить сообщение
    
    # Задержка перед показом информации о классе
    await asyncio.sleep(MESSAGE_DELAY)
    
    # Пытаемся отправить картинку класса
    image_path = f"images/{image_name}"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=description,
            reply_markup=get_class_confirmation_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            description,
            reply_markup=get_class_confirmation_keyboard()
        )
    
    await state.set_state(RegistrationStates.confirming_class)
    await callback.answer()

# Обработка кнопки "Назад к выбору классов"
@start_router.callback_query(F.data == "back_to_classes")
async def back_to_classes(callback: CallbackQuery, state: FSMContext):
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Задержка перед возвратом к выбору
    await asyncio.sleep(MESSAGE_DELAY)
    
    # Пытаемся отправить картинку выбора класса
    image_path = "images/classes.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption="🎯 Выбери класс персонажа:\n\n"
                   "🛠️ **Работяга** - мастер на все руки\n"
                   "💼 **Менеджер** - специалист по продажам\n"
                   "📱 **Блоггер** - разорившийся инфлюенсер с фанатами",
            reply_markup=get_classes_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            "🎯 Выбери класс персонажа:\n\n"
            "🛠️ **Работяга** - мастер на все руки\n"
            "💼 **Менеджер** - специалист по продажам\n"
            "📱 **Блоггер** - разорившийся инфлюенсер с фанатами",
            reply_markup=get_classes_keyboard()
        )
    
    await state.set_state(RegistrationStates.choosing_class)
    await callback.answer()

# Обработка кнопки "Выбрать этот класс" (переход к подтверждению)
@start_router.callback_query(F.data == "confirm_class")
async def confirm_class_selection(callback: CallbackQuery, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    character_name = data.get('character_name')
    character_class = data.get('character_class')
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Задержка перед подтверждением
    await asyncio.sleep(MESSAGE_DELAY)
    
    # Пытаемся отправить картинку подтверждения
    image_path = "images/confirmation.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"🎯 **Подтверждение выбора**\n\n"
                   f"📛 Имя: {character_name}\n"
                   f"🎯 Класс: {character_class}\n\n"
                   f"❗️ Вы уверены, что хотите выбрать этот класс?\n"
                   f"После подтверждения изменить класс будет невозможно!",
            reply_markup=get_final_confirmation_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            f"🎯 **Подтверждение выбора**\n\n"
            f"📛 Имя: {character_name}\n"
            f"🎯 Класс: {character_class}\n\n"
            f"❗️ Вы уверены, что хотите выбрать этот класс?\n"
            f"После подтверждения изменить класс будет невозможно!",
            reply_markup=get_final_confirmation_keyboard()
        )
    
    await state.set_state(RegistrationStates.final_confirmation)
    await callback.answer()

# Обработка кнопки "Вернуться к классам" (из подтверждения)
@start_router.callback_query(F.data == "back_to_class_info")
async def back_to_class_info(callback: CallbackQuery, state: FSMContext):
    # Получаем данные о выбранном классе
    data = await state.get_data()
    class_type = data.get('class_type')
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Задержка перед возвратом
    await asyncio.sleep(MESSAGE_DELAY)
    
    # Создаем новый callback с нужными данными для вызова choose_class
    class CallbackMock:
        def __init__(self, original_callback, class_type):
            self.message = original_callback.message
            self.from_user = original_callback.from_user
            self.data = f"class_{class_type}"
            self.id = original_callback.id
    
    mock_callback = CallbackMock(callback, class_type)
    
    # Возвращаем к информации о классе
    await choose_class(mock_callback, state)
    await callback.answer()

# Обработка финального подтверждения выбора
@start_router.callback_query(F.data == "final_confirm")
async def final_confirmation(callback: CallbackQuery, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    character_name = data.get('character_name')
    character_class = data.get('character_class')
    class_type = data.get('class_type')
    player_gender = data.get('player_gender', 'male')  # ← ДОБАВЛЕНО: получаем пол
    
    # Добавляем пользователя в БД
    user_id = callback.from_user.id
    username = callback.from_user.username
    first_name = callback.from_user.first_name
    last_name = callback.from_user.last_name
    
    user_db_id = db.add_user(user_id, username, first_name, last_name)
    
    # Создаем персонажа с учетом пола ← ИЗМЕНЕНО: передаем пол в БД
    if user_db_id:
        # TODO: Обновить метод add_player в Database для приема пола
        player_id = db.add_player(user_db_id, character_name, character_class, player_gender)
    
    # Удаляем кнопки из предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Задержка перед сообщением об успехе
    await asyncio.sleep(MESSAGE_DELAY)
    
    # Пытаемся отправить картинку успешной регистрации
    image_path = "images/registration_success.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    # Клавиатура с одной кнопкой "Начать играть"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    start_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Начать играть", callback_data="start_tutorial")]
    ])
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"🎉 Персонаж создан!\n\n"
                   f"📛 **Имя:** {character_name}\n"
                   f"🎯 **Класс:** {character_class}\n\n"
                   f"Чтобы начать играть нажмите кнопку ниже:",
            reply_markup=start_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            f"🎉 Персонаж создан!\n\n"
            f"📛 **Имя:** {character_name}\n"
            f"🎯 **Класс:** {character_class}\n\n"
            f"Чтобы начать играть нажмите кнопку ниже:",
            reply_markup=start_keyboard
        )
    
    # Очищаем состояние
    await state.clear()
    await callback.answer()

    # Обработка кнопки "Продолжить играть"
# Обработка кнопки "Продолжить играть" - ИСПРАВЛЕННАЯ ВЕРСИЯ
@start_router.callback_query(F.data == "continue_playing")
async def continue_playing(callback: CallbackQuery, state: FSMContext):
    """Продолжение игры с существующим персонажем"""
    user_id = callback.from_user.id
    
    # Получаем активного персонажа
    active_player = db.get_active_player(user_id)
    if not active_player:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    player_id = active_player[0]
    player_name = active_player[2]
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Проверяем прогресс обучения
    tutorial_progress = tutorial_db.get_tutorial_progress(player_id)
    
    if tutorial_progress:
        # Восстанавливаем обучение с последнего шага
        current_step = tutorial_progress[0]  # current_step
        player_balance = tutorial_progress[3]  # player_balance
        
        print(f"🔄 Восстанавливаем прогресс: {current_step}, баланс: {player_balance}")
        
        # Восстанавливаем состояние
        await state.update_data(player_id=player_id, player_balance=player_balance)
        
        # В зависимости от текущего шага восстанавливаем соответствующий этап
        if current_step == "waiting_for_belt_start":
            await state.set_state(TutorialStates.waiting_for_belt_start)
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔧 Подготовка материалов", callback_data="belt_prepare_materials")]
            ])
            await callback.message.answer(
                f"👋 С возвращением, {player_name}!\nПродолжим изготовление ремня.",
                reply_markup=keyboard
            )
            
        elif current_step == "in_shop_menu":
            # Если находимся в магазине, показываем меню магазина
            await state.set_state(TutorialStates.in_shop_menu)
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Вернуться в магазин", callback_data="view_showcase")]
            ])
            await callback.message.answer(
                f"👋 С возвращением, {player_name}!\nВы находились в магазине.",
                reply_markup=keyboard
            )
            
        elif current_step == "waiting_for_exit":
            # Если только что вышли из магазина
            await state.set_state(TutorialStates.waiting_for_exit)
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔨 Сделать ремень", callback_data="make_belt")]
            ])
            await callback.message.answer(
                f"👋 С возвращением, {player_name}!\nВы только что вышли из магазина.",
                reply_markup=keyboard
            )
            
        else:
            # Для других состояний начинаем с начала крафта
            await state.set_state(TutorialStates.waiting_for_belt_start)
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔧 Начать изготовление ремня", callback_data="belt_prepare_materials")]
            ])
            await callback.message.answer(
                f"👋 С возвращением, {player_name}!\nПродолжим изготовление ремня.",
                reply_markup=keyboard
            )
    else:
        # Начинаем обучение заново
        await start_tutorial_handler(callback, state)
    
    await callback.answer()

# Обработка кнопки "Создать нового"
@start_router.callback_query(F.data == "create_new_character")
async def create_new_character(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    active_player = db.get_active_player(user_id)
    
    if not active_player:
        await start_new_character_creation(callback, state)
        return
    
    # Показываем подтверждение для создания нового
    await show_new_character_confirmation(callback, active_player, state)

# Обработка подтверждения создания нового
@start_router.callback_query(F.data == "confirm_new_character")
async def confirm_new_character(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    old_player_id = data.get('old_player_id')
    
    if old_player_id:
        db.deactivate_player(old_player_id)
        tutorial_db.clear_tutorial_data(old_player_id)
    
    await callback.message.edit_reply_markup(reply_markup=None)
    await start_new_character_creation(callback, state)

# Обработка отмены создания нового
@start_router.callback_query(F.data == "cancel_new_character")  
async def cancel_new_character(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Действие отменено", reply_markup=get_existing_players_keyboard())
    await state.clear()

# Обработка кнопки "Профиль"
@start_router.callback_query(F.data == "view_profile")
async def view_profile(callback: CallbackQuery, state: FSMContext):
    """Просмотр профиля персонажа"""
    user_id = callback.from_user.id
    
    # Получаем активного персонажа
    active_player = db.get_active_player(user_id)
    if not active_player:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Извлекаем данные персонажа
    player_id = active_player[0]
    player_name = active_player[2]
    player_class = active_player[3]
    level = active_player[4]
    mastery = active_player[5]
    luck = active_player[6] 
    marketing = active_player[7]
    reputation = active_player[8]
    coins = active_player[9]
    gender = active_player[11] if len(active_player) > 11 else "male"
    
    # Формируем сообщение профиля
    gender_emoji = "👨" if gender == "male" else "👩"
    profile_text = (
        f"{gender_emoji} **Профиль персонажа**\n\n"
        f"📛 **Имя:** {player_name}\n"
        f"🎯 **Класс:** {player_class}\n"
        f"⭐ **Уровень:** {level}\n\n"
        f"📊 **Характеристики:**\n"
        f"• 🛠️ Мастерство: {mastery}\n"
        f"• 🍀 Удача: {luck}\n"
        f"• 📈 Маркетинг: {marketing}\n"
        f"• 💫 Репутация: {reputation}\n\n"
        f"💰 **Баланс:** {coins} монет"
    )
    
    # Удаляем кнопки из предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Отправляем профиль с кнопками управления
    image_path = "images/profile.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=profile_text,
            reply_markup=get_profile_management_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            profile_text,
            reply_markup=get_profile_management_keyboard()
        )
    
    await state.set_state(PlayerManagementStates.viewing_profile)
    await callback.answer()

# Обработка кнопки "Удалить персонажа" в профиле
@start_router.callback_query(F.data == "delete_character")
async def delete_character(callback: CallbackQuery, state: FSMContext):
    """Подтверждение удаления персонажа"""
    user_id = callback.from_user.id
    
    # Получаем активного персонажа
    active_player = db.get_active_player(user_id)
    if not active_player:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    player_name = active_player[2]
    
    # Удаляем кнопки из предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Отправляем подтверждение удаления
    image_path = "images/delete_confirmation.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"⚠️ **Подтверждение удаления**\n\n"
                   f"Вы действительно хотите удалить персонажа **{player_name}**?\n\n"
                   f"❗️ Это действие нельзя отменить! Все прогресс и предметы будут потеряны.",
            reply_markup=get_deletion_confirmation_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            f"⚠️ **Подтверждение удаления**\n\n"
            f"Вы действительно хотите удалить персонажа **{player_name}**?\n\n"
            f"❗️ Это действие нельзя отменить! Все прогресс и предметы будут потеряны.",
            reply_markup=get_deletion_confirmation_keyboard()
        )
    
    await state.set_state(PlayerManagementStates.confirming_deletion)
    await callback.answer()

# Обработка подтверждения удаления
@start_router.callback_query(F.data == "confirm_deletion")
async def confirm_deletion(callback: CallbackQuery, state: FSMContext):
    """Финальное подтверждение удаления"""
    user_id = callback.from_user.id
    
    # Получаем активного персонажа
    active_player = db.get_active_player(user_id)
    if not active_player:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    player_name = active_player[2]
    
    # Удаляем кнопки из предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Отправляем финальное подтверждение
    image_path = "images/final_delete.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"🚨 **ФИНАЛЬНОЕ ПОДТВЕРЖДЕНИЕ**\n\n"
                   f"Вы собираетесь УДАЛИТЬ персонажа **{player_name}** навсегда!\n\n"
                   f"❌ Все данные будут безвозвратно удалены\n"
                   f"❌ Прогресс обучения будет сброшен\n"
                   f"❌ Предметы и монеты будут потеряны\n\n"
                   f"Вы уверены?",
            reply_markup=get_final_deletion_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            f"🚨 **ФИНАЛЬНОЕ ПОДТВЕРЖДЕНИЕ**\n\n"
            f"Вы собираетесь УДАЛИТЬ персонажа **{player_name}** навсегда!\n\n"
            f"❌ Все данные будут безвозвратно удалены\n"
            f"❌ Прогресс обучения будет сброшен\n"
            f"❌ Предметы и монеты будут потеряны\n\n"
            f"Вы уверены?",
            reply_markup=get_final_deletion_keyboard()
        )
    
    await callback.answer()

# Обработка финального подтверждения удаления
@start_router.callback_query(F.data == "final_confirm_deletion")
async def final_confirm_deletion(callback: CallbackQuery, state: FSMContext):
    """Выполнение удаления персонажа"""
    user_id = callback.from_user.id
    
    # Получаем активного персонажа
    active_player = db.get_active_player(user_id)
    if not active_player:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    player_id = active_player[0]
    player_name = active_player[2]
    
    # Удаляем данные обучения
    tutorial_db.clear_tutorial_data(player_id)
    
    # Деактивируем персонажа
    db.deactivate_player(player_id)
    
    # Удаляем кнопки из предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Сообщение об успешном удалении
    image_path = "images/deletion_success.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"🗑️ Персонаж **{player_name}** был удален.\n\n"
                   f"Все данные персонажа были безвозвратно удалены.",
            reply_markup=get_registration_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            f"🗑️ Персонаж **{player_name}** был удален.\n\n"
            f"Все данные персонажа были безвозвратно удалены.",
            reply_markup=get_registration_keyboard()
        )
    
    await state.clear()
    await callback.answer()

# Обработка отмены удаления
@start_router.callback_query(F.data == "cancel_deletion")
async def cancel_deletion(callback: CallbackQuery, state: FSMContext):
    """Отмена удаления персонажа"""
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("✅ Удаление отменено")
    await state.clear()

# Обработка отмены финального удаления  
@start_router.callback_query(F.data == "cancel_final_deletion")
async def cancel_final_deletion(callback: CallbackQuery, state: FSMContext):
    """Отмена финального подтверждения удаления"""
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("✅ Удаление отменено")
    await state.clear()

# Обработка кнопки "Создать нового" - ПРОСТОЙ И ПОНЯТНЫЙ
@start_router.callback_query(F.data == "create_new_character")
async def create_new_character(callback: CallbackQuery, state: FSMContext):
    """Создание нового персонажа с подтверждением"""
    user_id = callback.from_user.id
    active_player = db.get_active_player(user_id)
    
    if not active_player:
        await start_new_character_creation(callback, state)
        return
    
    # Показываем подтверждение для создания нового
    await show_new_character_confirmation(callback, active_player, state)

# Вспомогательная функция - показ подтверждения
async def show_new_character_confirmation(callback: CallbackQuery, active_player: tuple, state: FSMContext):
    """Показывает подтверждение создания нового персонажа"""
    player_name = active_player[2]
    player_class = active_player[3]
    player_level = active_player[4]
    
    await callback.answer()
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        print(f"⚠️ Не удалось удалить кнопки: {e}")
    
    await asyncio.sleep(MESSAGE_DELAY)
    
    # Текст подтверждения
    confirmation_text = (
        f"⚠️ **ПОДТВЕРЖДЕНИЕ СОЗДАНИЯ НОВОГО ПЕРСОНАЖА**\n\n"
        f"У вас уже есть активный персонаж:\n"
        f"📛 **{player_name}**\n"
        f"🎯 **{player_class}** (Уровень {player_level})\n\n"
        f"🚨 **ВНИМАНИЕ!**\n"
        f"При создании нового персонажа:\n"
        f"• Текущий персонаж будет деактивирован\n"
        f"• Весь прогресс будет потерян\n"
        f"• Предметы и монеты будут сброшены\n"
        f"• Данные обучения удалятся\n"
        f"• Восстановление невозможно!\n\n"
        f"Вы уверены, что хотите продолжить?"
    )
    
    # Клавиатура подтверждения
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить и создать нового", callback_data="confirm_new_character")],
        [InlineKeyboardButton(text="❌ Нет, оставить текущего", callback_data="cancel_new_character")]
    ])
    
    image_path = "images/delete_warning.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=confirmation_text,
            reply_markup=confirmation_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            confirmation_text,
            reply_markup=confirmation_keyboard
        )
    
    # Сохраняем ID старого персонажа для удаления
    await state.update_data(old_player_id=active_player[0])

# Вспомогательная функция - начало создания нового персонажа
async def start_new_character_creation(callback: CallbackQuery, state: FSMContext):
    """Запускает процесс создания нового персонажа"""
    await asyncio.sleep(MESSAGE_DELAY)
    
    image_path = "images/create_character.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption="🎭 Отлично! Давай создадим твоего нового персонажа!\n\n"
                   "Как зовут твоего будущего кожевника?\n"
                   "(Выбери уникальное имя от 2 до 20 символов)",
        )
    except Exception as e:
        await callback.message.answer(
            "🎭 Отлично! Давай создадим твоего нового персонажа!\n\n"
            "Как зовут твоего будущего кожевника?\n"
            "(Выбери уникальное имя от 2 до 20 символов)",
        )
    
    await state.set_state(RegistrationStates.waiting_for_name)

# Обработка подтверждения создания нового
@start_router.callback_query(F.data == "confirm_new_character")
async def confirm_new_character(callback: CallbackQuery, state: FSMContext):
    """Подтвержденное создание нового персонажа"""
    data = await state.get_data()
    old_player_id = data.get('old_player_id')
    
    # Удаляем старого персонажа если он есть
    if old_player_id:
        db.deactivate_player(old_player_id)
        tutorial_db.clear_tutorial_data(old_player_id)
        print(f"🗑️ Удален старый персонаж: {old_player_id}")
    
    # Удаляем кнопки из сообщения подтверждения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        print(f"⚠️ Не удалось удалить кнопки: {e}")
    
    await callback.answer("✅ Начинаем создание нового персонажа!")
    
    # Запускаем создание нового
    await start_new_character_creation(callback, state)

# Обработка отмены создания нового  
@start_router.callback_query(F.data == "cancel_new_character")
async def cancel_new_character(callback: CallbackQuery, state: FSMContext):
    """Отмена создания нового персонажа"""
    # Удаляем кнопки из сообщения подтверждения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        print(f"⚠️ Не удалось удалить кнопки: {e}")
    
    # Очищаем состояние
    await state.clear()
    
    await callback.answer("✅ Создание нового персонажа отменено")
    
    # Возвращаем к выбору действий
    await asyncio.sleep(MESSAGE_DELAY)
    await callback.message.answer(
        "Что вы хотите сделать?",
        reply_markup=get_existing_players_keyboard()
    )

# Функция запуска обучения
async def start_tutorial(callback: CallbackQuery, state: FSMContext):
    """Запускает обучение для нового игрока"""
    user_id = callback.from_user.id
    
    # Получаем активного персонажа
    active_player = db.get_active_player(user_id)
    if not active_player:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    player_id = active_player[0]  # ID персонажа
    player_name = active_player[2]  # имя персонажа
    player_class = active_player[3]  # класс персонажа
    
    # Инициализируем прогресс обучения для этого персонажа
    tutorial_db.init_tutorial_progress(player_id)
    tutorial_db.init_shop_items()
    
    # Определяем предысторию по классу
    if player_class == "Работяга":
        backstory = f"Вы пол жизни трудитесь на заводе. Работа не легкая, но честная. Каждый день, как часы, с 8:00 до 17:00 вы у станка. А после смены остается время на себя. Посмотреть сериал, погулять по городу с семьей, встретиться с друзьями. Обычная спокойная жизнь.\n\nОднажды вечером, листая ленту YouTube, вы наткнулись на видео, где мастер из куска кожи делал ремешок, а потом кошелек, а потом сумку. Так ловко и просто. Вам захотелось тоже попробовать сделать себе ремень. А если получится, то и сумку.\n\nВзяв часть накоплений, вы отправились в ближайший магазин, где продавали натуральную кожу."
        image_name = "worker_backstory.jpg"
    
    elif player_class == "Менеджер":
        backstory = f"Вы были обычным офисным работником, чьи дни проходили в бесконечных совещаниях и работе с таблицами. Вы чувствовали, как тонете в корпоративной рутине, где ваша инициатива никому не нужна, а реальные результаты работы размыты и абстрактны. Мир, состоящий из цифр и отчетов, казался вам пустым и лишенным смысла.\n\nДля отдыха вы смотрете YouTube, и однажды он подсунул вам канал кожевника. Ловко и просто мастер делал разные вещи. И что вам понравилось, результат своих трудов мастер мог подержать в руках, а что еще лучше – пользоваться им каждый день! Тогда вы решил попробовать и самостоятельно, что-то сделать у себя на кухне.\n\nВзяв часть накоплений, вы отправились в ближайший магазин, где продавали кожу."
        image_name = "manager_backstory.jpg"
    
    else:  # Блоггер
        backstory = f"Вы когда-то были известным блогером с тысячами подписчиков, строя свою жизнь на лайках и одобрении аудитории. Однако неудачное вложение в стартап обернулся финансовым крахом и блокировкой всех ваших соцсетей. В одночасье вы потеряли всё, что считали своей жизнью, осознав шаткость мира, построенного на чужих оценках.\n\nВ поисках нового пути вы обнаружили на YouTube сообщество мастеров-ремесленников. Их кропотливая работа с кожей, создание классных вещей, поразила вас. Это был шанс начать всё с чистого листа и построить не виртуальный, а реальный, осязаемый бизнес.\n\nВзяв часть накоплений, вы отправились в ближайший магазин, где продавали кожу."
        image_name = "blogger_backstory.jpg"
    
    # Удаляем кнопки из предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Пытаемся отправить картинку предыстории
    image_path = f"images/tutorial/{image_name}"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=backstory,
            reply_markup=get_tutorial_start_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            backstory,
            reply_markup=get_tutorial_start_keyboard()
        )
    
    await state.set_state(TutorialStates.waiting_for_shop_enter)
    await state.update_data(player_id=player_id)
    await callback.answer()
    
# Заглушки для главного меню (реализуем позже)
@start_router.callback_query(F.data == "work_menu")
async def work_menu(callback: CallbackQuery):
    await callback.answer("🛠️ Система работы скоро будет доступна!")

@start_router.callback_query(F.data == "orders_menu")
async def orders_menu(callback: CallbackQuery):
    await callback.answer("📋 Система заказов скоро будет доступна!")

@start_router.callback_query(F.data == "settings")
async def settings(callback: CallbackQuery):
    await callback.answer("⚙️ Настройки скоро будут доступны!")

async def return_to_last_step(callback: CallbackQuery, state: FSMContext, player_id, current_step, player_balance):
    """Возвращает игрока на последний шаг обучения"""
    user_id = callback.from_user.id
    active_player = db.get_active_player(user_id)
    player_name = active_player[2] if active_player else "Игрок"
    
    # Восстанавливаем состояние
    await state.update_data(player_id=player_id, player_balance=player_balance)
    
    # ОТПРАВЛЯЕМ НОВОЕ СООБЩЕНИЕ ВМЕСТО РЕДАКТИРОВАНИЯ СТАРОГО
    if current_step == "waiting_for_shop_enter":
        await state.set_state(TutorialStates.waiting_for_shop_enter)
        tutorial_db.update_tutorial_progress(player_id, "waiting_for_shop_enter")
        
        image_path = "images/tutorial/return.jpg"
        if not os.path.exists(image_path):
            image_path = "images/placeholder.jpg"
        
        try:
            photo = FSInputFile(image_path)
            await callback.message.answer_photo(
                photo=photo,
                caption=f"👋 С возвращением, {player_name}!\n\nПродолжим с того места, где ты остановился.",
                reply_markup=get_tutorial_start_keyboard()
            )
        except:
            await callback.message.answer(
                f"👋 С возвращением, {player_name}!\n\nПродолжим с того места, где ты остановился.",
                reply_markup=get_tutorial_start_keyboard()
            )
    
    elif current_step == "waiting_for_approach":
        await state.set_state(TutorialStates.waiting_for_approach)
        tutorial_db.update_tutorial_progress(player_id, "waiting_for_approach")
        
        image_path = "images/tutorial/shop_entrance.jpg"
        if not os.path.exists(image_path):
            image_path = "images/placeholder.jpg"
        
        try:
            photo = FSInputFile(image_path)
            await callback.message.answer_photo(
                photo=photo,
                caption=f"👋 С возвращением в магазин, {player_name}!\n\nТы остановился когда рассматривал инструменты.",
                reply_markup=get_approach_keyboard()
            )
        except:
            await callback.message.answer(
                f"👋 С возвращением в магазин, {player_name}!\n\nТы остановился когда рассматривал инструменты.",
                reply_markup=get_approach_keyboard()
            )
    
    elif current_step == "waiting_for_oldman_approach":
        await state.set_state(TutorialStates.waiting_for_oldman_approach)
        tutorial_db.update_tutorial_progress(player_id, "waiting_for_oldman_approach")
        
        image_path = "images/tutorial/oldman_talking.jpg"
        if not os.path.exists(image_path):
            image_path = "images/placeholder.jpg"
        
        try:
            photo = FSInputFile(image_path)
            await callback.message.answer_photo(
                photo=photo,
                caption=f"👋 С возвращением, {player_name}!\n\nТы как раз подошел послушать Гену.",
                reply_markup=get_oldman_approach_keyboard()
            )
        except:
            await callback.message.answer(
                f"👋 С возвращением, {player_name}!\n\nТы как раз подошел послушать Гену.",
                reply_markup=get_oldman_approach_keyboard()
            )
    
    elif current_step == "waiting_for_showcase":
        await state.set_state(TutorialStates.waiting_for_showcase)
        tutorial_db.update_tutorial_progress(player_id, "waiting_for_showcase")
        
        image_path = "images/tutorial/shop_showcase.jpg"
        if not os.path.exists(image_path):
            image_path = "images/placeholder.jpg"
        
        try:
            photo = FSInputFile(image_path)
            await callback.message.answer_photo(
                photo=photo,
                caption=f"👋 С возвращением, {player_name}!\n\nГена как раз предлагал посмотреть на витрину.",
                reply_markup=get_showcase_keyboard()
            )
        except:
            await callback.message.answer(
                f"👋 С возвращением, {player_name}!\n\nГена как раз предлагал посмотреть на витрину.",
                reply_markup=get_showcase_keyboard()
            )
    
    elif current_step in ["in_shop_menu", "in_shop_category", "waiting_for_exit"]:
        await state.set_state(TutorialStates.in_shop_menu)
        tutorial_db.update_tutorial_progress(player_id, "in_shop_menu")
        
        image_path = "images/tutorial/tools_showcase.jpg"
        if not os.path.exists(image_path):
            image_path = "images/placeholder.jpg"
        
        try:
            photo = FSInputFile(image_path)
            await callback.message.answer_photo(
                photo=photo,
                caption=f"👋 С возвращением в магазин, {player_name}!\n\n💰 Ваш баланс: {player_balance} монет\nПродолжи покупки:",
                reply_markup=get_shop_menu_keyboard(player_balance)
            )
        except:
            await callback.message.answer(
                f"👋 С возвращением в магазин, {player_name}!\n\n💰 Ваш баланс: {player_balance} монет\nПродолжи покупки:",
                reply_markup=get_shop_menu_keyboard(player_balance)
            )
 
    
    else:
        await start_tutorial(callback, state)
