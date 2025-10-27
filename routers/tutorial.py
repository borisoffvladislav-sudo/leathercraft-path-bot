# routers/tutorial.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.models import Database, tutorial_db
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot
from aiogram.types import Message
import json
import os
import asyncio

tutorial_router = Router()
db = Database()

# Команда для администратора для перемещения по этапам
@tutorial_router.message(Command("setstage"))
async def set_stage_command(message: Message, state: FSMContext, bot: Bot):
    """Команда для перемещения персонажа на нужный этап (только для администратора)"""
    
    # Проверяем, что пользователь администратор (замени на свой ID)
    ADMIN_IDS = [1092273052]  # Замени на свой Telegram ID
    
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Эта команда только для администратора")
        return
    
    # Получаем аргументы команды
    args = message.text.split()[1:]
    
    if len(args) < 2:
        await message.answer(
            "📋 Использование: /setstage [player_id] [stage_name]\n\n"
            "📝 Примеры этапов:\n"
            "• waiting_for_shop_enter - Начало магазина\n"
            "• in_shop_menu - Магазин обучения\n"
            "• waiting_for_belt_start - Начало крафта ремня\n"
            "• waiting_for_belt_materials - Выбор кожи\n"
            "• in_shop_after_tutorial - Магазин после обучения\n"
            "• waiting_for_holder_start - Начало картхолдера\n"
        )
        return
    
    try:
        player_id = int(args[0])
        stage_name = args[1]
        
        # Получаем активного игрока
        active_player = db.get_active_player(message.from_user.id)
        if not active_player:
            await message.answer("❌ Активный персонаж не найден")
            return
        
        # Обновляем прогресс
        tutorial_db.update_tutorial_progress(player_id, stage_name)
        
        # Очищаем состояние FSM
        await state.clear()
        
        # Устанавливаем новое состояние
        state_class = getattr(TutorialStates, stage_name, None)
        if state_class:
            await state.set_state(state_class)
            await state.update_data(player_id=player_id)
        
        await message.answer(f"✅ Персонаж {player_id} перемещен на этап: {stage_name}")
        
        # Показываем доступные состояния
        all_states = [state for state in TutorialStates.__all_states__]
        states_info = "\n".join([f"• {state.state}" for state in all_states[:10]])  # первые 10
        
        await message.answer(f"📋 Доступные состояния:\n{states_info}\n... и другие")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")

# Команда для просмотра текущего прогресса
@tutorial_router.message(Command("progress"))
async def check_progress_command(message: Message):
    """Команда для проверки текущего прогресса"""
    
    ADMIN_IDS = [1092273052]  # Замени на свой Telegram ID
    
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Эта команда только для администратора")
        return
    
    # Получаем активного игрока
    active_player = db.get_active_player(message.from_user.id)
    if not active_player:
        await message.answer("❌ Активный персонаж не найден")
        return
    
    player_id = active_player[0]
    progress = tutorial_db.get_tutorial_progress(player_id)
    
    if progress:
        stage, step, completed, balance = progress
        await message.answer(
            f"📊 Прогресс персонажа {player_id}:\n"
            f"• Этап: {stage}\n"
            f"• Шаг: {step}\n"
            f"• Баланс: {balance} монет\n"
            f"• Завершено: {completed}"
        )
    else:
        await message.answer("❌ Прогресс не найден")

# Белые списки товаров для обучения
AVAILABLE_TUTORIAL_ITEMS = {
    "Ножи": ["Канцелярский нож"],
    "Пробойники": ["Высечные пробойники"],
    "Торцбилы": ["Мультитул 3 в 1"],
    "Материалы": ["Дешевая ременная заготовка", "Пчелиный воск"],
    "Фурнитура": ["Дешевая фурнитура для ремней"],
    "Нитки": ["Швейные МосНитки"]
}

# Состояния для обучения
class TutorialStates(StatesGroup):
    waiting_for_shop_enter = State()
    waiting_for_approach = State()
    waiting_for_oldman_approach = State()
    waiting_for_showcase = State()
    in_shop_menu = State()
    in_shop_category = State()
    waiting_for_exit = State()
     # === НОВЫЕ СОСТОЯНИЯ ДЛЯ КРАФТА ===
    waiting_for_belt_start = State()           # Этап 1 - Сделать ремень
    waiting_for_belt_materials = State()       # Этап 2 - Подготовка материалов
    waiting_for_belt_leather = State()         # Этап 3 - Выбор кожи
    waiting_for_belt_hardware = State()        # Этап 4 - Выбор фурнитуры
    waiting_for_belt_tools = State()           # Этап 5 - Выбор инструментов
    waiting_for_belt_assembly = State()        # Этап 6 - Установить пряжку
    waiting_for_belt_quality = State()         # Этап 7-8 - Оценить результат
    waiting_for_belt_sleep = State()           # Этап 9 - Отправиться спать
    
    waiting_for_shop_return = State()          # Этап 10 - В магазин
    waiting_for_shop_view = State()            # Этап 11 - Посмотреть витрину
    in_shop_after_tutorial = State()           # Этап 11 - Магазин (все товары)
    waiting_for_holder_start = State()         # Этап 13 - Приступить
    waiting_for_holder_leather = State()       # Этап 14 - Выбор кожи
    waiting_for_holder_tools = State()         # Этап 15 - Выбор инструментов
    waiting_for_holder_threads = State()       # Этап 16 - Выбор ниток
    waiting_for_holder_quality = State()       # Этап 17-18 - Оценить/Подарить
    waiting_for_holder_final = State()         # Этап 19 - Завершение
    # === СОСТОЯНИЯ ДЛЯ ТРЕТЬЕЙ ЧАСТИ ОБУЧЕНИЯ (СУМКА) ===
    waiting_for_bag_start = State()              # Этап 20
    in_shop_bag_materials = State()              # Этап 21
    waiting_for_bag_materials_selection = State() # Этап 22
    waiting_for_bag_tools_selection = State()    # Этап 23
    waiting_for_bag_wax_selection = State()      # Этап 24
    waiting_for_bag_threads_selection = State()  # Этап 25
    waiting_for_bag_quality_1 = State()          # Этап 26-27
    waiting_for_bag_retry = State()              # Этап 28
    in_shop_bag_retry = State()                  # Этап 29
    waiting_for_bag_retry_start = State()        # Этап 30
    waiting_for_bag_retry_materials = State()    # Этап 31
    waiting_for_bag_retry_tools = State()        # Этап 32
    waiting_for_bag_retry_wax = State()          # Этап 33
    waiting_for_bag_retry_threads = State()      # Этап 34
    waiting_for_bag_quality_2 = State()          # Этап 35-36
    waiting_for_final = State()                  # Этап 37

# Клавиатура для начала обучения
def get_tutorial_start_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Зайти в магазин", callback_data="enter_shop")]
    ])
    return keyboard

# Клавиатура для подхода к мужичку
def get_approach_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👣 Подойти поближе", callback_data="approach_closer")]
    ])
    return keyboard

# Клавиатура для подхода к Гене
def get_oldman_approach_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👋 Подойти к мужичку", callback_data="approach_oldman")]
    ])
    return keyboard

# Клавиатура для просмотра витрины
def get_showcase_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👀 Посмотреть на витрину", callback_data="view_showcase")]
    ])
    return keyboard

# Клавиатура меню магазина
def get_shop_menu_keyboard(balance=2000):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔪 Ножи", callback_data="shop_knives")],
        [InlineKeyboardButton(text="🕳️ Пробойники", callback_data="shop_punches")],
        [InlineKeyboardButton(text="🔧 Торцбилы", callback_data="shop_edges")],
        [InlineKeyboardButton(text="🧵 Материалы", callback_data="shop_materials")],
        [InlineKeyboardButton(text="📎 Фурнитура", callback_data="shop_hardware")],
        [InlineKeyboardButton(text="🚪 Выйти из магазина", callback_data="shop_exit")]
    ])
    return keyboard

# Клавиатура для кнопки "Сделать ремень"
def get_make_belt_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔨 Сделать ремень", callback_data="make_belt")]
    ])
    return keyboard

# Обработка кнопки "Сделать ремень" - Этап 1
@tutorial_router.callback_query(F.data == "make_belt")
async def make_belt_handler(callback: CallbackQuery, state: FSMContext):
    """Начало изготовления ремня - Этап 1"""
    print("🎯 ОТЛАДКА: Обработчик make_belt вызван")
    
    # Получаем данные игрока
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        # Если player_id нет в состоянии, получаем из БД
        active_player = db.get_active_player(callback.from_user.id)
        if active_player:
            player_id = active_player[0]
            await state.update_data(player_id=player_id)
            print(f"✅ player_id получен из БД: {player_id}")
        else:
            await callback.answer("❌ Ошибка: персонаж не найден")
            return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_belt_start")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        print("✅ Кнопки удалены")
    except Exception as e:
        print(f"⚠️ Не удалось удалить кнопки: {e}")
    
    # Текст для этапа 1
    stage1_text = (
        "Вернувшись домой, вы распаковал все инструменты. Долго игрались с насадками мультитула, "
        "рассматривали пробойники. Ременную ленту крутили в руках: пытались растянуть, наматывали "
        "на локоть, прикидывали по талии.\n\n"
        "Наигравшись, включили видео на Youtube, которое рекомендовал Гена, и стали повторять за ведущим."
    )
    
    # Клавиатура для перехода к следующему этапу
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    stage1_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Подготовка материалов", callback_data="belt_prepare_materials")]
    ])
    
    # Отправляем сообщение этапа 1
    image_path = "images/tutorial/belt_start.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage1_text,
            reply_markup=stage1_keyboard
        )
        print("✅ Сообщение этапа 1 отправлено")
    except Exception as e:
        await callback.message.answer(
            stage1_text,
            reply_markup=stage1_keyboard
        )
        print("✅ Сообщение этапа 1 отправлено (без фото)")
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_belt_start)
    await callback.answer()
    print("✅ Состояние установлено: waiting_for_belt_start")

# Обработка кнопки "Подготовка материалов" - Этап 2
@tutorial_router.callback_query(F.data == "belt_prepare_materials")
async def belt_prepare_materials(callback: CallbackQuery, state: FSMContext):
    """Подготовка материалов для ремня - Этап 2"""
    print("🎯 ОТЛАДКА: belt_prepare_materials вызван")
    
    # Получаем данные игрока
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_belt_materials")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        print("✅ Кнопки удалены")
    except Exception as e:
        print(f"⚠️ Не удалось удалить кнопки: {e}")
    
    # Текст для этапа 2
    stage2_text = (
        "Блоггер начал с душной лекции, как выбрать правильно ленту. Чем дешевые отличаются от дорогих "
        "и что-то про урезы. Отдельно про пряжки и винты. Вы бы купили дорогие ленты, если не боялись их испортить.\n\n"
        "Возьмите заготовки которые купили в магазине.\n"
        "- Сейчас у вас в инвентаре есть только дешевая ременная лента. В будущем у вас их будет больше "
        "материалов в инвентаре и вы сможете выбирать использовать для заказа.\n\n"
        "Нажмите «Дешевая ременная лента», чтобы продолжить"
    )
    
    # Получаем инвентарь игрока
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    leather_items = [item[0] for item in inventory if "ременная" in item[0].lower()]
    
    print(f"🎒 ОТЛАДКА: Найдены кожи в инвентаре: {leather_items}")
    
    # Создаем клавиатуру с доступными кожами - ИСПРАВЛЕННЫЙ КОД
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard_buttons = []
    for item_name in leather_items:
        # ИСПРАВЛЕНИЕ: используем короткие callback_data
        if item_name == "Дешевая ременная заготовка":
            callback_data = "select_leather_cheap"  # ✅ КОРОТКИЙ callback_data
        else:
            # Для других кож тоже используем короткие названия
            short_name = item_name.lower().replace(' ', '_').replace('дешевая', 'cheap').replace('ременная', 'belt').replace('заготовка', 'leather')[:20]
            callback_data = f"select_leather_{short_name}"
        
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🧵 {item_name}", 
            callback_data=callback_data  # ✅ КОРОТКИЙ callback_data
        )])
    
    stage2_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    print(f"⌨️ ОТЛАДКА: Создана клавиатура с кнопками: {[btn[0].text for btn in keyboard_buttons]}")
    print(f"⌨️ ОТЛАДКА: Callback_data: {[btn[0].callback_data for btn in keyboard_buttons]}")
    
    # Отправляем сообщение этапа 2
    image_path = "images/tutorial/belt_materials.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage2_text,
            reply_markup=stage2_keyboard
        )
        print("✅ Сообщение этапа 2 отправлено с фото")
    except Exception as e:
        print(f"⚠️ Ошибка отправки фото: {e}")
        # Попробуем отправить без фото
        try:
            await callback.message.answer(
                stage2_text,
                reply_markup=stage2_keyboard
            )
            print("✅ Сообщение этапа 2 отправлено (без фото)")
        except Exception as e2:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e2}")
            # Отправляем сообщение без клавиатуры
            await callback.message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте позже."
            )
            return
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_belt_leather)
    await callback.answer()
    print("✅ Состояние установлено: waiting_for_belt_leather")

# Обработка выбора кожи для ремня - Этап 3
@tutorial_router.callback_query(F.data.startswith("select_leather_"))
async def select_belt_leather(callback: CallbackQuery, state: FSMContext):
    """Выбор кожи для ремня - Этап 3"""
    print("🎯 ОТЛАДКА: select_belt_leather вызван")
    
    # Получаем данные игрока
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем короткий код кожи из callback_data
    leather_code = callback.data.replace("select_leather_", "")
    print(f"🎒 ОТЛАДКА: Получен код кожи: {leather_code}")
    
    # Преобразуем код в полное название
    leather_map = {
        "cheap": "Дешевая ременная заготовка",
        # добавьте другие коды по мере необходимости
    }
    
    leather_name = leather_map.get(leather_code, "Дешевая ременная заготовка")  # по умолчанию
    
    print(f"🎒 ОТЛАДКА: Выбрана кожа: {leather_name}")
    
    # Сохраняем выбранную кожу в состоянии
    await state.update_data(selected_leather=leather_name)
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_belt_leather")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        print("✅ Кнопки удалены")
    except:
        print("⚠️ Не удалось удалить кнопки")
    
    # Текст для этапа 3
    stage3_text = "Теперь выберите фурнитуру"
    
    # Получаем инвентарь игрока
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    hardware_items = [item[0] for item in inventory if "фурнитура" in item[0].lower()]
    
    print(f"🎒 ОТЛАДКА: Найдена фурнитура в инвентаре: {hardware_items}")
    
    # Создаем клавиатуру с доступной фурнитурой (тоже с короткими callback_data)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard_buttons = []
    for item_name in hardware_items:
        # Используем короткие callback_data для фурнитуры
        if item_name == "Дешевая фурнитура для ремней":
            callback_data = "select_hardware_cheap"
        else:
            callback_data = f"select_hardware_{item_name.replace(' ', '_').lower()[:15]}"
        
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"📎 {item_name}", 
            callback_data=callback_data
        )])
    
    stage3_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    print(f"⌨️ ОТЛАДКА: Создана клавиатура фурнитуры: {[btn[0].text for btn in keyboard_buttons]}")
    
    # Отправляем сообщение этапа 3
    image_path = "images/tutorial/belt_hardware.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage3_text,
            reply_markup=stage3_keyboard
        )
        print("✅ Сообщение этапа 3 отправлено с фото")
    except Exception as e:
        print(f"⚠️ Ошибка отправки фото: {e}")
        await callback.message.answer(
            stage3_text,
            reply_markup=stage3_keyboard
        )
        print("✅ Сообщение этапа 3 отправлено (без фото)")
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_belt_hardware)
    await callback.answer(f"✅ Выбрано: {leather_name}")
    print("✅ Состояние установлено: waiting_for_belt_hardware")

# Обработка выбора фурнитуры для ремня - Этап 4
@tutorial_router.callback_query(F.data.startswith("select_hardware_"))
async def select_belt_hardware(callback: CallbackQuery, state: FSMContext):
    """Выбор фурнитуры для ремня - Этап 4"""
    # Получаем данные игрока
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем название выбранной фурнитуры
    hardware_name = callback.data.replace("select_hardware_", "").replace("_", " ")
    
    # Сохраняем выбранную фурнитуру в состоянии
    await state.update_data(selected_hardware=hardware_name)
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_belt_hardware")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 4
    stage4_text = (
        "Блоггер продолжил рассказывать о том, какие инструменты понадобятся. Он показывал овальные пробойники, "
        "отсекатели для концов ремня, прозрачные шаблоны по которым все размечать можно. Вы видели их в магазине, "
        "да пока решили не тратиться.\n\n"
        "Подготовьте инструменты, которые купили в магазине"
    )
    
    # Клавиатура для перехода к выбору инструментов
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    stage4_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠️ Выбрать инструменты", callback_data="belt_select_tools")]
    ])
    
    # Отправляем сообщение этапа 4
    image_path = "images/tutorial/belt_tools.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage4_text,
            reply_markup=stage4_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage4_text,
            reply_markup=stage4_keyboard
        )
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_belt_tools)
    await callback.answer(f"✅ Выбрано: {hardware_name}")

# Обработка кнопки "Выбрать инструменты" - Этап 5
@tutorial_router.callback_query(F.data == "belt_select_tools")
async def belt_select_tools(callback: CallbackQuery, state: FSMContext):
    """Выбор инструментов для ремня - Этап 5"""
    # Получаем данные игрока
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_belt_tools")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Получаем инвентарь игрока
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    
    # Фильтруем только инструменты
    tool_items = []
    for item in inventory:
        item_name = item[0]
        # Ищем инструменты по ключевым словам
        if any(keyword in item_name.lower() for keyword in ["нож", "пробойник", "мультитул", "торцбил"]):
            tool_items.append(item_name)
    
    # Инициализируем список выбранных инструментов в состоянии
    await state.update_data(selected_tools=[])
    
    # Создаем клавиатуру для выбора инструментов
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard_buttons = []
    for tool_name in tool_items:
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🔘 {tool_name}", 
            callback_data=f"toggle_tool_{tool_name.replace(' ', '_')}"
        )])
    
    # Кнопка продолжения (пока неактивна - нужно выбрать все инструменты)
    keyboard_buttons.append([InlineKeyboardButton(
        text="⏭️ Продолжить (выберите все инструменты)", 
        callback_data="tools_not_selected"
    )])
    
    tools_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Текст для этапа 5
    stage5_text = (
        "Выберите инструменты из инвентаря. На этом этапе игрок выбирает все, которые у него есть.\n\n"
        "По мере выбора, рядом с названием смайлик с красным кружком меняется на зеленую галочку. "
        "При повторном нажатии – выбор отменяется.\n\n"
        "После выбора всех трех инструментов (нож, мультитул и высечной пробойник) нажмите «Продолжить»"
    )
    
    # Отправляем сообщение этапа 5
    image_path = "images/tutorial/tools_selection.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage5_text,
            reply_markup=tools_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage5_text,
            reply_markup=tools_keyboard
        )
    
    # Устанавливаем состояние выбора инструментов
    await state.set_state(TutorialStates.waiting_for_belt_tools)
    await callback.answer()

# Обработка toggle выбора инструментов - Этап 5
@tutorial_router.callback_query(F.data.startswith("toggle_tool_"))
async def toggle_tool_selection(callback: CallbackQuery, state: FSMContext):
    """Toggle выбор/отмена выбора инструмента"""
    # Получаем данные из состояния
    data = await state.get_data()
    player_id = data.get('player_id')
    selected_tools = data.get('selected_tools', [])
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем название инструмента
    tool_name = callback.data.replace("toggle_tool_", "").replace("_", " ")
    
    # Toggle выбор инструмента
    if tool_name in selected_tools:
        # Убираем из выбранных
        selected_tools.remove(tool_name)
        await callback.answer(f"❌ {tool_name} - выбор отменен")
    else:
        # Добавляем в выбранные
        selected_tools.append(tool_name)
        await callback.answer(f"✅ {tool_name} - выбран")
    
    # Сохраняем обновленный список в состоянии
    await state.update_data(selected_tools=selected_tools)
    
    # Получаем инвентарь игрока для обновления клавиатуры
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    tool_items = []
    for item in inventory:
        item_name = item[0]
        if any(keyword in item_name.lower() for keyword in ["нож", "пробойник", "мультитул", "торцбил"]):
            tool_items.append(item_name)
    
    # Создаем обновленную клавиатуру
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard_buttons = []
    for tool_name in tool_items:
        # Определяем эмодзи в зависимости от выбора
        emoji = "✅" if tool_name in selected_tools else "🔘"
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"{emoji} {tool_name}", 
            callback_data=f"toggle_tool_{tool_name.replace(' ', '_')}"
        )])
    
    # Проверяем, выбраны ли все обязательные инструменты
    required_tools = ["Канцелярский нож", "Мультитул 3 в 1", "Высечные пробойники"]
    all_required_selected = all(tool in selected_tools for tool in required_tools)
    
    # Кнопка продолжения (активна только если выбраны все инструменты)
    if all_required_selected:
        keyboard_buttons.append([InlineKeyboardButton(
            text="⏭️ Продолжить", 
            callback_data="belt_tools_confirmed"
        )])
    else:
        keyboard_buttons.append([InlineKeyboardButton(
            text="⏭️ Продолжить (выберите все инструменты)", 
            callback_data="tools_not_selected"
        )])
    
    updated_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Обновляем сообщение с новой клавиатурой
    try:
        await callback.message.edit_reply_markup(reply_markup=updated_keyboard)
    except Exception as e:
        print(f"⚠️ Не удалось обновить клавиатуру: {e}")
        await callback.answer("Обновите сообщение")

# Обработка попытки продолжить без выбора всех инструментов
@tutorial_router.callback_query(F.data == "tools_not_selected")
async def tools_not_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка попытки продолжить без выбора всех инструментов"""
    # Получаем данные из состояния
    data = await state.get_data()
    selected_tools = data.get('selected_tools', [])
    
    # Проверяем какие инструменты не выбраны
    required_tools = ["Канцелярский нож", "Мультитул 3 в 1", "Высечные пробойники"]
    missing_tools = [tool for tool in required_tools if tool not in selected_tools]
    
    if missing_tools:
        missing_text = ", ".join(missing_tools)
        await callback.answer(f"❌ Не выбраны: {missing_text}", show_alert=True)
    else:
        await callback.answer("✅ Все инструменты выбраны, можно продолжать")

# Обработка подтверждения выбора инструментов - Этап 6
@tutorial_router.callback_query(F.data == "belt_tools_confirmed")
async def belt_tools_confirmed(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора инструментов и переход к сборке - Этап 6"""
    # Получаем данные игрока
    data = await state.get_data()
    player_id = data.get('player_id')
    selected_tools = data.get('selected_tools', [])
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Проверяем что выбраны все обязательные инструменты
    required_tools = ["Канцелярский нож", "Мультитул 3 в 1", "Высечные пробойники"]
    if not all(tool in selected_tools for tool in required_tools):
        await callback.answer("❌ Выберите все обязательные инструменты", show_alert=True)
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_belt_assembly")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 6
    stage6_text = (
        "Вы приступили к работе, повторяя все за блоггером. На удивление, в жизни все оказалось сложнее чем на видео. "
        "Прорезать ленту канцелярским ножом оказалось не так просто. Мультитул снимал фаску с трудом, задирая местами кожу. "
        "Иногда он врезался слишком сильно вглубь ленты, и вы думали, что теперь ее можно выбросить.\n\n"
        "Шаг за шагом, вы повторяли движения: полировали края и настало время установить пряжку"
    )
    
    # Клавиатура для установки пряжки
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    stage6_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔩 Установить пряжку", callback_data="belt_install_buckle")]
    ])
    
    # Отправляем сообщение этапа 6
    image_path = "images/tutorial/belt_assembly.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage6_text,
            reply_markup=stage6_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage6_text,
            reply_markup=stage6_keyboard
        )
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_belt_assembly)
    await callback.answer("✅ Инструменты выбраны!")

# Обработка кнопки "Установить пряжку" - Этап 7
@tutorial_router.callback_query(F.data == "belt_install_buckle")
async def belt_install_buckle(callback: CallbackQuery, state: FSMContext):
    """Установка пряжки на ремень - Этап 7"""
    # Получаем данные игрока
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_belt_quality")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 7
    stage7_text = (
        "Толи винтики короткие, толи вы что-то делаете не так, но у вас ушло около 20 минут "
        "на установку пряжки и прикручивание винтов."
    )
    
    # Клавиатура для оценки результата
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    stage7_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Оценить результат", callback_data="belt_evaluate_quality")]
    ])
    
    # Отправляем сообщение этапа 7
    image_path = "images/tutorial/belt_buckle.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage7_text,
            reply_markup=stage7_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage7_text,
            reply_markup=stage7_keyboard
        )
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_belt_quality)
    await callback.answer()

# Обработка кнопки "Оценить результат" - Этап 8
@tutorial_router.callback_query(F.data == "belt_evaluate_quality")
async def belt_evaluate_quality(callback: CallbackQuery, state: FSMContext):
    """Оценка качества ремня - Этап 8"""
    # Получаем данные игрока
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_belt_sleep")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Сообщение с качеством
    quality_text = "🎉Качество заказа – Сносное🎉"
    
    # Отправляем сообщение с качеством
    image_path = "images/tutorial/quality_snosnoe.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=quality_text
        )
    except Exception as e:
        await callback.message.answer(quality_text)
    
    # Ждем 2 секунды и отправляем следующее сообщение
    await asyncio.sleep(2)
    
    # Текст после оценки качества
    stage8_text = (
        "«Могло быть и хуже» – подумали вы. Местами резанули лишнего, торцбилом порвали края местами. "
        "Отверстие под пряжку немного косое. Но в целом, вы чувствуете, тепло на душе от того, что это сделали ВЫ. "
        "Да криво, да косо, у блоггера на видео сильно аккуратнее, но для первого раза не плохо.\n\n"
        "Довольные собой вы отправились спать"
    )
    
    # Клавиатура для перехода ко сну
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    stage8_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😴 Отправиться спать", callback_data="belt_go_to_sleep")]
    ])
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage8_text,
            reply_markup=stage8_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage8_text,
            reply_markup=stage8_keyboard
        )
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_belt_sleep)
    await callback.answer()

# Обработка кнопки "Отправиться спать" - Этап 9
@tutorial_router.callback_query(F.data == "belt_go_to_sleep")
async def belt_go_to_sleep(callback: CallbackQuery, state: FSMContext):
    """Завершение дня и переход к следующему дню - Этап 9"""
    # Получаем данные игрока
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_shop_return")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 9
    stage9_text = (
        "На следующий день, вы встретились с друзьями и рассказали о том, что сами сделали ремень. "
        "Показали пару фото на фоне обоев и один из друзей предложил ему сделать картхолдер.\n\n"
        "Это уже интересно. Правда у вас нет нужных инструментов и кожи. Пора вновь в магазин."
    )
    
    # Клавиатура для перехода в магазин
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    stage9_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏪 Отправиться в магазин", callback_data="return_to_shop")]
    ])
    
    # Отправляем сообщение этапа 9
    image_path = "images/tutorial/friends_meeting.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage9_text,
            reply_markup=stage9_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage9_text,
            reply_markup=stage9_keyboard
        )
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_shop_return)
    await callback.answer()

# Обработка кнопки "Отправиться в магазин" - Этап 10
@tutorial_router.callback_query(F.data == "return_to_shop")
async def return_to_shop(callback: CallbackQuery, state: FSMContext):
    """Возврат в магазин после изготовления ремня - Этап 10"""
    # Получаем данные игрока
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_shop_view")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 10
    stage10_text = (
        "Ничего не изменилось. Сотрудницы бегают туда-сюда, не обращая на вас внимание. "
        "У кассы Геннадий Борисович, что-то активно доказывал кассиру. Проходя мимо него, "
        "вы услышали, что он что-то говорит про летающий молот. Возможно, по этому виду спорта у него КМС!"
    )
    
    # Клавиатура для просмотра витрины
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    stage10_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👀 Посмотреть витрину", callback_data="view_shop_after_tutorial")]
    ])
    
    # Отправляем сообщение этапа 10
    image_path = "images/tutorial/shop_return.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage10_text,
            reply_markup=stage10_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage10_text,
            reply_markup=stage10_keyboard
        )
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_shop_view)
    await callback.answer()

# Обработка кнопки "Посмотреть витрину" - Этап 11 - ИСПРАВЛЕННАЯ ВЕРСИЯ
@tutorial_router.callback_query(F.data == "view_shop_after_tutorial")
async def view_shop_after_tutorial(callback: CallbackQuery, state: FSMContext):
    """Просмотр витрины магазина после обучения - Этап 11"""
    print("🎯 ОТЛАДКА: view_shop_after_tutorial вызван")
    
    # Получаем данные игрока
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "in_shop_after_tutorial")
    
    # Получаем баланс игрока
    progress = tutorial_db.get_tutorial_progress(player_id)
    balance = progress[3] if progress else 2000
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        print("✅ Кнопки удалены")
    except Exception as e:
        print(f"⚠️ Не удалось удалить кнопки: {e}")
    
    # Текст для этапа 11
    stage11_text = "Добрый день, что вы хотели бы приобрести?"
    
    # Создаем клавиатуру магазина (ВСЕ товары доступны) с правильными иконками
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    # Получаем ВСЕ категории товаров с правильными иконками
    all_categories = [
        ("🔪 Ножи", "shop_after_knives"),
        ("🕳️ Пробойники", "shop_after_punches"), 
        ("🔧 Торцбилы", "shop_after_edges"),
        ("🧵 Материалы", "shop_after_materials"),
        ("📎 Фурнитура", "shop_after_hardware"),
        ("🧶 Нитки", "shop_after_threads"),  # Новая категория с новой иконкой
        ("🧪 Химия", "shop_after_chemistry")  # Новая категория с новой иконкой
    ]
    
    keyboard_buttons = []
    for category_text, callback_data in all_categories:
        keyboard_buttons.append([InlineKeyboardButton(
            text=category_text, 
            callback_data=callback_data
        )])
    
    keyboard_buttons.append([InlineKeyboardButton(
        text="🚪 Выйти из магазина", 
        callback_data="shop_after_exit"
    )])
    
    shop_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    print(f"⌨️ ОТЛАДКА: Создана клавиатура магазина после обучения")
    
    # Отправляем сообщение этапа 11
    image_path = "images/tutorial/shop_after_tutorial.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"{stage11_text}\n\n💰 Ваш баланс: {balance} монет",
            reply_markup=shop_keyboard
        )
        print("✅ Сообщение этапа 11 отправлено с фото")
    except Exception as e:
        print(f"⚠️ Ошибка отправки фото: {e}")
        await callback.message.answer(
            f"{stage11_text}\n\n💰 Ваш баланс: {balance} монет",
            reply_markup=shop_keyboard
        )
        print("✅ Сообщение этапа 11 отправлено (без фото)")
    
    # Устанавливаем состояние магазина после обучения
    await state.set_state(TutorialStates.in_shop_after_tutorial)
    await state.update_data(player_balance=balance)
    await callback.answer()
    print("✅ Состояние установлено: in_shop_after_tutorial")

# Обработка категорий магазина после обучения - Этап 11 - ИСПРАВЛЕННАЯ ВЕРСИЯ
@tutorial_router.callback_query(F.data.startswith("shop_after_") & ~F.data.in_(["shop_after_exit"]))
async def show_shop_after_category(callback: CallbackQuery, state: FSMContext):
    """Показ категорий товаров в магазине после обучения с фильтрацией покупок"""
    print(f"🎯 ОТЛАДКА: show_shop_after_category вызван с {callback.data}")
    
    category_map = {
        "shop_after_knives": "Ножи",
        "shop_after_punches": "Пробойники", 
        "shop_after_edges": "Торцбилы",
        "shop_after_materials": "Материалы",
        "shop_after_hardware": "Фурнитура",
        "shop_after_threads": "Нитки",
        "shop_after_chemistry": "Химия"
    }
    
    category = category_map.get(callback.data)
    if not category:
        print(f"❌ Ошибка: неизвестная категория {callback.data}")
        await callback.answer("❌ Ошибка категории")
        return
    
    print(f"🎯 ОТЛАДКА: Открываем категорию после обучения: {category}")
    
    # Получаем данные игрока
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем баланс
    progress = tutorial_db.get_tutorial_progress(player_id)
    balance = progress[3] if progress else 2000
    
    # Получаем ВСЕ товары категории из БД
    all_category_items = tutorial_db.get_shop_items_by_category(category)
    
    # СПИСОК РАЗРЕШЕННЫХ ТОВАРОВ ДЛЯ КАРТХОЛДЕРА
    ALLOWED_ITEMS = [
        "Строчные пробойники PFG",      # категория "Пробойники"
        "Кожа для галантереи (дешевая)", # категория "Материалы"  
        "Швейные МосНитки"              # категория "Нитки"
    ]
    
    # Создаем клавиатуру со ВСЕМИ товарами, но с разными callback_data
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    for item in all_category_items:
        item_name = item[0]
        item_price = item[1]
        
        can_afford = balance >= item_price
        is_allowed = item_name in ALLOWED_ITEMS
        
        item_text = f"{item_name} - {item_price} монет"
        
        if not can_afford:
            item_text += " ❌"
        elif not is_allowed:
            item_text += " 🔒"
        
        # Определяем callback_data в зависимости от доступности
        if not is_allowed:
            # Товар не разрешен для покупки
            callback_data = "not_needed"
        elif not can_afford:
            # Не хватает денег
            callback_data = "cant_afford"
        else:
            # Можно купить
            short_name = item_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('строчные', 'line').replace('пробойники', 'punch').replace('кожа', 'leather').replace('галантереи', 'galanterey').replace('швейные', 'sewing').replace('моснитки', 'mos').replace('для', 'for')[:20]
            callback_data = f"buy_after_{short_name}"
        
        builder.button(
            text=item_text,
            callback_data=callback_data
        )
    
    builder.button(text="🔙 Назад", callback_data="back_to_shop_after_menu")
    builder.adjust(1)
    keyboard = builder.as_markup()
    
    # Обновляем сообщение
    try:
        await callback.message.edit_caption(
            caption=f"🏪 Магазин - {category}\n\n"
                   f"💰 Ваш баланс: {balance} монет\n"
                   f"📋 Все товары (🔒 - сейчас не нужны):\n"
                   f"Выберите товар:",
            reply_markup=keyboard
        )
        print(f"✅ Категория {category} обновлена (фильтрация покупок применена)")
    except Exception as e:
        print(f"❌ Ошибка обновления категории: {e}")
        await callback.answer("❌ Ошибка обновления")
        return
    
    await state.update_data(current_category=category, player_balance=balance)
    await callback.answer()

# Обработка кнопки "Назад" в магазине после обучения
@tutorial_router.callback_query(F.data == "back_to_shop_after_menu")
async def back_to_shop_after_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню магазина после обучения - РЕДАКТИРОВАНИЕ текущего сообщения"""
    print("🎯 ОТЛАДКА: back_to_shop_after_menu вызван - редактирование текущего сообщения")
    
    try:
        data = await state.get_data()
        player_id = data.get('player_id')
        
        progress = tutorial_db.get_tutorial_progress(player_id)
        balance = progress[3] if progress else 2000
        
        # Полный список всех категорий
        all_categories = [
            ("🔪 Ножи", "shop_after_knives"),
            ("🕳️ Пробойники", "shop_after_punches"), 
            ("🔧 Торцбилы", "shop_after_edges"),
            ("🧵 Материалы", "shop_after_materials"),
            ("📎 Фурнитура", "shop_after_hardware"),
            ("🧶 Нитки", "shop_after_threads"),
            ("🧪 Химия", "shop_after_chemistry")
        ]
        
        keyboard_buttons = []
        for category_text, callback_data in all_categories:
            keyboard_buttons.append([InlineKeyboardButton(
                text=category_text, 
                callback_data=callback_data
            )])
        
        keyboard_buttons.append([InlineKeyboardButton(
            text="🚪 Выйти из магазина", 
            callback_data="shop_after_exit"
        )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        # РЕДАКТИРУЕМ текущее сообщение вместо создания нового
        await callback.message.edit_caption(
            caption=f"Добрый день, что вы хотели бы приобрести?\n\n💰 Ваш баланс: {balance} монет",
            reply_markup=keyboard
        )
        
        print("✅ Успешный возврат в главное меню (редактирование сообщения)")
        await callback.answer()
        
    except Exception as e:
        print(f"❌ Ошибка в back_to_shop_after_menu: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

# Обработка нажатия на заблокированные товары в магазине после обучения
@tutorial_router.callback_query(F.data == "not_needed")
async def not_needed_item(callback: CallbackQuery):
    """Обработка нажатия на ненужные товары"""
    await callback.answer("❌ Сейчас мне это не нужно", show_alert=True)

# Обработка покупки товаров в магазине после обучения
@tutorial_router.callback_query(F.data.startswith("buy_after_"))
async def buy_after_tutorial(callback: CallbackQuery, state: FSMContext):
    """Покупка товаров в магазине после обучения"""
    print(f"🎯 ОТЛАДКА: buy_after_tutorial вызван с {callback.data}")
    
    try:
        data = await state.get_data()
        player_id = data.get('player_id')
        current_category = data.get('current_category', '')
        
        if not player_id:
            await callback.answer("❌ Ошибка: персонаж не найден")
            return
        
        # Получаем короткое название товара из callback_data
        short_name = callback.data.replace("buy_after_", "")
        print(f"🛒 ОТЛАДКА: Короткое название товара: {short_name}")
        
        # Получаем текущий баланс
        progress = tutorial_db.get_tutorial_progress(player_id)
        balance = progress[3] if progress else 2000
        
        # Получаем ВСЕ товары категории
        all_category_items = tutorial_db.get_shop_items_by_category(current_category)
        print(f"📦 ОТЛАДКА: Все товары в категории {current_category}:")
        for item in all_category_items:
            print(f"  - {item[0]}")
        
        # Ищем товар по короткому названию
        short_to_full_map = {
            "line_punch_pfg": "Строчные пробойники PFG",
            "leather_for_galanter": "Кожа для галантереи (дешевая)",
            "leather_galanterey": "Кожа для галантереи (дешевая)", 
            "sewing_mos": "Швейные МосНитки"
        }

        full_item_name = short_to_full_map.get(short_name)
        item_info = None
        
        if full_item_name:
            for item in all_category_items:
                if item[0] == full_item_name:
                    item_info = item
                    break
        
        # ЕСЛИ ТОВАР НЕ НАЙДЕН - ВЫХОДИМ
        if not item_info:
            print(f"❌ Товар не найден: {short_name}")
            await callback.answer("❌ Товар не найден")
            return
        
        item_name = item_info[0]
        item_price = item_info[1]
        
        print(f"✅ Найден товар: {item_name} за {item_price} монет")
        
        # Проверяем баланс
        if balance < item_price:
            await callback.answer("❌ Недостаточно монет!")
            return
        
        # Проверяем инвентарь на дубликаты
        inventory = tutorial_db.get_tutorial_inventory(player_id)
        for inv_item in inventory:
            if len(inv_item) > 0 and inv_item[0] == item_name:
                await callback.answer("❌ У тебя уже есть этот предмет!")
                return
        
        # Выполняем покупку
        new_balance = balance - item_price
        success = tutorial_db.add_to_tutorial_inventory(player_id, item_name, current_category)
        
        if success:
            # Обновляем баланс
            tutorial_db.update_player_balance(player_id, new_balance)
            
            # Обновляем сообщение магазина
            await update_shop_after_category_message(callback, current_category, new_balance, f"✅ Куплено: {item_name}")
            
            await state.update_data(player_balance=new_balance)
            await callback.answer(f"✅ Куплено: {item_name}")
            print(f"✅ Успешная покупка: {item_name}")
        else:
            await callback.answer("❌ Ошибка при покупке")
            print(f"❌ Ошибка при добавлении в инвентарь: {item_name}")
            
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА в buy_after_tutorial: {str(e)}")
        import traceback
        traceback.print_exc()
        await callback.answer("❌ Ошибка при покупке")

# Вспомогательная функция для обновления сообщения магазина после обучения
async def update_shop_after_category_message(callback: CallbackQuery, category: str, balance: int, status_message: str = ""):
    """Обновляет сообщение категории магазина после обучения"""
    all_category_items = tutorial_db.get_shop_items_by_category(category)
    
    # ДОБАВЛЯЕМ СПИСОК РАЗРЕШЕННЫХ ТОВАРОВ
    ALLOWED_ITEMS = [
        "Строчные пробойники PFG",
        "Кожа для галантереи (дешевая)", 
        "Швейные МосНитки"
    ]
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    for item in all_category_items:
        item_name = item[0]
        item_price = item[1]
        
        can_afford = balance >= item_price
        is_allowed = item_name in ALLOWED_ITEMS  # ПРОВЕРЯЕМ РАЗРЕШЕНИЕ
        
        item_text = f"{item_name} - {item_price} монет"
        
        if not can_afford:
            item_text += " ❌"
        elif not is_allowed:
            item_text += " 🔒"  # ЗАМОК ДЛЯ НЕРАЗРЕШЕННЫХ ТОВАРОВ
        
        # Определяем callback_data в зависимости от доступности
        if not is_allowed:
            callback_data = "not_needed"
        elif not can_afford:
            callback_data = "cant_afford"
        else:
            short_name = item_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('строчные', 'line').replace('пробойники', 'punch').replace('кожа', 'leather').replace('галантереи', 'galanterey').replace('швейные', 'sewing').replace('моснитки', 'mos').replace('для', 'for')[:20]
            callback_data = f"buy_after_{short_name}"
        
        builder.button(
            text=item_text,
            callback_data=callback_data
        )
    
    builder.button(text="🔙 Назад", callback_data="back_to_shop_after_menu")
    builder.adjust(1)
    keyboard = builder.as_markup()
    
    caption = f"🏪 Магазин - {category}\n\n"
    if status_message:
        caption += f"{status_message}\n"
    caption += f"💰 Ваш баланс: {balance} монет\nВыберите товар:"
    
    await callback.message.edit_caption(
        caption=caption,
        reply_markup=keyboard
    )

# Обработка кнопки "Приступить" для картхолдера - Этап 14 (ПОЛНАЯ ВЕРСИЯ)
@tutorial_router.callback_query(F.data == "start_holder")
async def start_holder_craft(callback: CallbackQuery, state: FSMContext):
    """Начало изготовления картхолдера - Этап 14"""
    print("🎯 ОТЛАДКА: start_holder_craft вызван")
    
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_holder_leather")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        print("✅ Кнопки удалены")
    except:
        print("⚠️ Не удалось удалить кнопки")
    
    # Текст для этапа 14
    stage14_text = "Выберите кожу из которой будете делать изделие"
    
    # Получаем инвентарь игрока (кожи для галантереи)
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    leather_items = [item[0] for item in inventory if any(keyword in item[0].lower() for keyword in ["кожа", "галантерея", "заготовка"])]
    
    print(f"🎒 ОТЛАДКА: Найдены кожи в инвентаре: {leather_items}")
    
    # Создаем клавиатуру с доступными кожами
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard_buttons = []
    for item_name in leather_items:
        # СОЗДАЕМ ПРОСТЫЕ И ПОНЯТНЫЕ КОДЫ ДЛЯ КАЖДОЙ КОЖИ
        if item_name == "Дешевая ременная заготовка":
            callback_data = "select_holder_leather_belt_cheap"
        elif item_name == "Обычная ременная заготовка":
            callback_data = "select_holder_leather_belt_mid"
        elif item_name == "Дорогая ременная заготовка":
            callback_data = "select_holder_leather_belt_pro"
        elif item_name == "Кожа для галантереи (дешевая)":
            callback_data = "select_holder_leather_galanterey_cheap"
        elif item_name == "Кожа для галантереи (средняя)":
            callback_data = "select_holder_leather_galanterey_mid"
        elif item_name == "Кожа для галантереи (дорогая)":
            callback_data = "select_holder_leather_galanterey_pro"
        elif item_name == "Кожа для сумок (дешевая)":
            callback_data = "select_holder_leather_bags_cheap"
        elif item_name == "Кожа для сумок (средняя)":
            callback_data = "select_holder_leather_bags_mid"
        elif item_name == "Кожа для сумок (дорогая)":
            callback_data = "select_holder_leather_bags_pro"
        else:
            # Для неизвестных кож используем общий формат
            short_name = item_name.lower().replace(' ', '_').replace('(', '').replace(')', '')[:15]
            callback_data = f"select_holder_leather_{short_name}"
    
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🧵 {item_name}", 
            callback_data=callback_data
        )])
    stage14_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    print(f"⌨️ ОТЛАДКА: Создана клавиатура выбора кожи: {[btn[0].text for btn in keyboard_buttons]}")
    print(f"⌨️ ОТЛАДКА: Callback_data кнопок: {[btn[0].callback_data for btn in keyboard_buttons]}")
    
    # Отправляем сообщение этапа 14
    image_path = "images/tutorial/holder_leather.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage14_text,
            reply_markup=stage14_keyboard
        )
        print("✅ Сообщение этапа 14 отправлено с фото")
    except Exception as e:
        print(f"⚠️ Ошибка отправки фото: {e}")
        await callback.message.answer(
            stage14_text,
            reply_markup=stage14_keyboard
        )
        print("✅ Сообщение этапа 14 отправлено (без фото)")
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_holder_leather)
    await callback.answer()
    print("✅ Состояние установлено: waiting_for_holder_leather")

# Обработка выхода из магазина после обучения - Этап 12-13
@tutorial_router.callback_query(F.data == "shop_after_exit")
async def shop_after_exit(callback: CallbackQuery, state: FSMContext):
    """Выход из магазина после обучения - Этап 12-13"""
    print("🎯 ОТЛАДКА: shop_after_exit вызван")
    
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    thread_items = [item[0] for item in inventory if "нитки" in item[0].lower()]
    
    print(f"🎒 ОТЛАДКА: Проверка ниток в инвентаре: {thread_items}")
    
    if not thread_items:
        # Если ниток нет - не пускаем и предлагаем купить
        await callback.answer(
            "❌ Вам нужны нитки для изготовления картхолдера! Купите нитки в категории 'Нитки'.",
            show_alert=True
        )
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_holder_start")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        print("✅ Кнопки удалены")
    except:
        print("⚠️ Не удалось удалить кнопки")
    
    # Текст для этапа 12-13
    stage13_text = "Закупив все необходимое, вы отправились домой делать картхолдер другу"
    
    # Клавиатура для начала изготовления картхолдера
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    # СОЗДАЕМ ПРОСТУЮ КНОПКУ С КОРОТКИМ callback_data
    stage13_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔨 Приступить", callback_data="start_holder")]
    ])
    
    print("⌨️ Создана кнопка 'Приступить' с callback_data: start_holder")
    
    # Отправляем сообщение этапа 13
    image_path = "images/tutorial/holder_start.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage13_text,
            reply_markup=stage13_keyboard
        )
        print("✅ Сообщение этапа 12-13 отправлено с кнопкой")
    except Exception as e:
        print(f"⚠️ Ошибка отправки фото: {e}")
        await callback.message.answer(
            stage13_text,
            reply_markup=stage13_keyboard
        )
        print("✅ Сообщение этапа 12-13 отправлено (без фото)")
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_holder_start)
    await callback.answer()
    print("✅ Состояние установлено: waiting_for_holder_start")

# Обработка выбора кожи для картхолдера - Этап 15 - ИСПРАВЛЕННАЯ ВЕРСИЯ
@tutorial_router.callback_query(F.data.startswith("select_holder_leather_"))
async def select_holder_leather(callback: CallbackQuery, state: FSMContext):
    """Выбор кожи для картхолдера - Этап 15"""
    print("🎯 ОТЛАДКА: select_holder_leather вызван")
    
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем код кожи из callback_data
    leather_code = callback.data.replace("select_holder_leather_", "")
    print(f"🎒 ОТЛАДКА: Получен код кожи: '{leather_code}'")
    
    # ПРОСТАЯ ПРОВЕРКА ПО СОДЕРЖАНИЮ НАЗВАНИЯ
    if "galanterey" in leather_code:
        # Это галантерейная кожа - подходит
        leather_name = "Кожа для галантереи"
        if "cheap" in leather_code:
            leather_name += " (дешевая)"
        elif "mid" in leather_code:
            leather_name += " (средняя)" 
        elif "pro" in leather_code:
            leather_name += " (дорогая)"
    elif "belt" in leather_code or "ременная" in leather_code:
        # Это ременная заготовка - НЕ подходит
        await callback.answer("❌ Этот материал не подходит для картхолдера! Выберите галантерейную кожу.", show_alert=True)
        return
    elif "bags" in leather_code or "сумок" in leather_code:
        # Это кожа для сумок - НЕ подходит  
        await callback.answer("❌ Этот материал не подходит для картхолдера! Выберите галантерейную кожу.", show_alert=True)
        return
    else:
        # Неизвестный материал
        await callback.answer("❌ Неизвестный материал", show_alert=True)
        return
    
    print(f"🎒 ОТЛАДКА: Определена кожа: {leather_name}")
    
    # Сохраняем выбранную кожу в состоянии
    await state.update_data(selected_holder_leather=leather_name)
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_holder_tools")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        print("✅ Кнопки удалены")
    except:
        print("⚠️ Не удалось удалить кнопки")
    
    # Текст для этапа 15
    stage15_text = (
        "Вы включили на фоне очередной ролик из интернета и приступили к работе. Какие инструменты вам понадобятся?\n\n"
        "- выберите Канцелярский нож, Строчные пробойники PFG, Мультитул 3в1"
    )
    
    # Получаем инвентарь игрока
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    
    # Фильтруем только инструменты
    tool_items = []
    for item in inventory:
        item_name = item[0]
        if any(keyword in item_name.lower() for keyword in ["нож", "пробойник", "мультитул", "торцбил"]):
            tool_items.append(item_name)
    
    # Инициализируем список выбранных инструментов в состоянии
    await state.update_data(selected_holder_tools=[])
    
    # Создаем клавиатуру для выбора инструментов
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard_buttons = []
    for tool_name in tool_items:
        # Используем простые callback_data
        if tool_name == "Канцелярский нож":
            callback_data = "toggle_holder_tool_knife"
        elif tool_name == "Строчные пробойники PFG":
            callback_data = "toggle_holder_tool_punch"
        elif tool_name == "Мультитул 3 в 1":
            callback_data = "toggle_holder_tool_multitool"
        elif tool_name == "Высечные пробойники":
            callback_data = "toggle_holder_tool_punch_set"
        else:
            callback_data = f"toggle_holder_tool_{tool_name.replace(' ', '_').lower()[:15]}"
        
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🔘 {tool_name}", 
            callback_data=callback_data
        )])
    
    # Кнопка продолжения (пока неактивна)
    keyboard_buttons.append([InlineKeyboardButton(
        text="⏭️ Продолжить (выберите нужные инструменты)", 
        callback_data="holder_tools_not_selected"
    )])
    
    tools_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем сообщение этапа 15
    image_path = "images/tutorial/holder_tools.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage15_text,
            reply_markup=tools_keyboard
        )
        print("✅ Сообщение этапа 15 отправлено с фото")
    except Exception as e:
        print(f"⚠️ Ошибка отправки фото: {e}")
        await callback.message.answer(
            stage15_text,
            reply_markup=tools_keyboard
        )
        print("✅ Сообщение этапа 15 отправлено (без фото)")
    
    # Устанавливаем состояние выбора инструментов
    await state.set_state(TutorialStates.waiting_for_holder_tools)
    await callback.answer(f"✅ Выбрано: {leather_name}")
    print("✅ Состояние установлено: waiting_for_holder_tools")

# Обработка toggle выбора инструментов для картхолдера - Этап 15
@tutorial_router.callback_query(F.data.startswith("toggle_holder_tool_"))
async def toggle_holder_tool_selection(callback: CallbackQuery, state: FSMContext):
    """Toggle выбор/отмена выбора инструмента для картхолдера"""
    data = await state.get_data()
    player_id = data.get('player_id')
    selected_tools = data.get('selected_holder_tools', [])
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # ИСПРАВЛЕНИЕ: Получаем код инструмента и преобразуем в полное название
    tool_code = callback.data.replace("toggle_holder_tool_", "")
    print(f"🔧 ОТЛАДКА: Получен код инструмента: '{tool_code}'")
    
    # ПРЕОБРАЗУЕМ КОД В ПОЛНОЕ НАЗВАНИЕ
    tool_map = {
        "knife": "Канцелярский нож",
        "punch": "Строчные пробойники PFG", 
        "multitool": "Мультитул 3 в 1",
        "punch_set": "Высечные пробойники"
    }
    
    # Получаем полное название инструмента
    tool_name = tool_map.get(tool_code)
    if not tool_name:
        # Если код не найден, используем как есть (для других инструментов)
        tool_name = tool_code.replace('_', ' ')
    
    print(f"🔧 ОТЛАДКА: Преобразовано в: '{tool_name}'")
    
    # Toggle выбор инструмента
    if tool_name in selected_tools:
        selected_tools.remove(tool_name)
        await callback.answer(f"❌ {tool_name} - выбор отменен")
    else:
        selected_tools.append(tool_name)
        await callback.answer(f"✅ {tool_name} - выбран")
    
    # Сохраняем обновленный список в состоянии
    await state.update_data(selected_holder_tools=selected_tools)
    
    # Получаем инвентарь игрока для обновления клавиатуры
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    tool_items = []
    for item in inventory:
        item_name = item[0]
        if any(keyword in item_name.lower() for keyword in ["нож", "пробойник", "мультитул", "торцбил"]):
            tool_items.append(item_name)
    
    # Создаем обновленную клавиатуру
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard_buttons = []
    for tool_name in tool_items:
        emoji = "✅" if tool_name in selected_tools else "🔘"
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"{emoji} {tool_name}", 
            callback_data=f"toggle_holder_tool_{tool_name.replace(' ', '_')}"
        )])
    
    # Проверяем выбранные инструменты
    required_tools = ["Канцелярский нож", "Строчные пробойники PFG", "Мультитул 3 в 1"]
    forbidden_tools = ["Высечные пробойники"]  # Запрещенные инструменты
    
    # Проверяем что выбраны все нужные и нет запрещенных
    all_required_selected = all(tool in selected_tools for tool in required_tools)
    has_forbidden_tools = any(tool in selected_tools for tool in forbidden_tools)
    
    if has_forbidden_tools:
        # Есть запрещенные инструменты - показываем ошибку
        keyboard_buttons.append([InlineKeyboardButton(
            text="❌ Отмените выбор высечного пробойника", 
            callback_data="holder_tools_not_selected"
        )])
    elif all_required_selected:
        # Все нужные инструменты выбраны, запрещенных нет
        keyboard_buttons.append([InlineKeyboardButton(
            text="⏭️ Продолжить", 
            callback_data="holder_tools_confirmed"
        )])
    else:
        # Не все нужные инструменты выбраны
        keyboard_buttons.append([InlineKeyboardButton(
            text="⏭️ Продолжить (выберите нужные инструменты)", 
            callback_data="holder_tools_not_selected"
        )])
    
    updated_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Обновляем сообщение с новой клавиатурой
    try:
        await callback.message.edit_reply_markup(reply_markup=updated_keyboard)
    except Exception as e:
        print(f"⚠️ Не удалось обновить клавиатуру: {e}")
        await callback.answer("Обновите сообщение")

# Обработка попытки продолжить без правильного выбора инструментов
@tutorial_router.callback_query(F.data == "holder_tools_not_selected")
async def holder_tools_not_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка попытки продолжить без правильного выбора инструментов"""
    data = await state.get_data()
    selected_tools = data.get('selected_holder_tools', [])
    
    required_tools = ["Канцелярский нож", "Срочные пробойники PFG", "Мультитул 3 в 1"]
    forbidden_tools = ["Высечные пробойники"]
    
    missing_tools = [tool for tool in required_tools if tool not in selected_tools]
    extra_tools = [tool for tool in forbidden_tools if tool in selected_tools]
    
    if missing_tools:
        missing_text = ", ".join(missing_tools)
        await callback.answer(f"❌ Не выбраны: {missing_text}", show_alert=True)
    elif extra_tools:
        await callback.answer("❌ Отмените выбор высечного пробойника - он не нужен", show_alert=True)
    else:
        await callback.answer("✅ Все инструменты выбраны правильно")

# Обработка подтверждения выбора инструментов для картхолдера - Этап 16
@tutorial_router.callback_query(F.data == "holder_tools_confirmed")
async def holder_tools_confirmed(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора инструментов для картхолдера - Этап 16"""
    data = await state.get_data()
    player_id = data.get('player_id')
    selected_tools = data.get('selected_holder_tools', [])
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Проверяем что выбраны все нужные инструменты и нет запрещенных
    required_tools = ["Канцелярский нож", "Строчные пробойники PFG", "Мультитул 3 в 1"]
    forbidden_tools = ["Высечные пробойники"]
    
    if not all(tool in selected_tools for tool in required_tools):
        await callback.answer("❌ Выберите все обязательные инструменты", show_alert=True)
        return
    
    if any(tool in selected_tools for tool in forbidden_tools):
        await callback.answer("❌ Отмените выбор высечного пробойника", show_alert=True)
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_holder_threads")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        print("✅ Кнопки удалены")
    except:
        print("⚠️ Не удалось удалить кнопки")
    
    # Текст для этапа 16
    stage16_text = (
        "По инструкции из ролика вы начали кроить деталли по линейке. получилось даже более менее сносно. линейка почти не съезжала. Сегодня даже фаски получилось снять мультитулом не так криво. Но чего вы точно не ожидали, так это грохота во время работы пробойником. Весь стол гремел в унисон вашим стукам \n"
        "Взглянув на результат пробития, вы около 2 часов потратили на то, чтобы найти информацию, как пробивать отверстия, чтобы на выходе была ровная строчка.\n"
        "Через 2 часа пришло время сшивать\n\n"
        "*- выберите нитки в инвентаре -*"
    )
    
    # Получаем инвентарь игрока (нитки)
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    thread_items = [item[0] for item in inventory if "нитки" in item[0].lower()]
    
    print(f"🎒 ОТЛАДКА: Найдены нитки в инвентаре: {thread_items}")
    
    # СОЗДАЕМ КЛАВИАТУРУ С ДОСТУПНЫМИ НИТКАМИ
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard_buttons = []
    for item_name in thread_items:
        # Используем короткие callback_data
        short_name = item_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('швейные', 'sewing').replace('моснитки', 'mos')[:20]
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🧵 {item_name}", 
            callback_data=f"select_thread_{short_name}"
        )])
    
    stage16_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    print(f"⌨️ ОТЛАДКА: Создана клавиатура выбора ниток: {[btn[0].text for btn in keyboard_buttons]}")
    
    # Отправляем сообщение этапа 16
    image_path = "images/tutorial/holder_stitch.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage16_text,
            reply_markup=stage16_keyboard
        )
        print("✅ Сообщение этапа 16 отправлено с фото")
    except Exception as e:
        print(f"⚠️ Ошибка отправки фото: {e}")
        await callback.message.answer(
            stage16_text,
            reply_markup=stage16_keyboard
        )
        print("✅ Сообщение этапа 16 отправлено (без фото)")
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_holder_threads)
    await callback.answer("✅ Инструменты выбраны!")
    print("✅ Состояние установлено: waiting_for_holder_threads")

# Обработка выбора ниток для картхолдера - Этап 17
@tutorial_router.callback_query(F.data.startswith("select_thread_"))
async def select_holder_threads(callback: CallbackQuery, state: FSMContext):
    """Выбор ниток для картхолдера - Этап 17"""
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем название выбранных ниток
    thread_name = callback.data.replace("select_thread_", "").replace("_", " ")
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_holder_quality")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 17
    stage17_text = (
        "Закончив прошивать холдер вы взглянули на результат работы и решили, что такое лучше никому не показывать.\n"
        "Кривой шов, страшный торец и следы клея, это явно не то, что стоит дарить друзьям.\n\n"
        "Отложив изделие в ящик, еще пару дней вы практиковались в изготовлении холдера.\n"
        "Хорошо, что кожи уходило не много и через неделю у вас получилось сделать что-то более-менее сносное"
    )
    
    # Клавиатура для оценки результата
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    stage17_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Оценить результат", callback_data="holder_evaluate_quality")]
    ])
    
    # Отправляем сообщение этапа 17
    image_path = "images/tutorial/holder_quality.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage17_text,
            reply_markup=stage17_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage17_text,
            reply_markup=stage17_keyboard
        )
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_holder_quality)
    await callback.answer(f"✅ Выбрано: {thread_name}")

# Обработка оценки качества картхолдера - Этап 18
@tutorial_router.callback_query(F.data == "holder_evaluate_quality")
async def holder_evaluate_quality(callback: CallbackQuery, state: FSMContext):
    """Оценка качества картхолдера - Этап 18"""
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_holder_gift")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    # ДОБАВЛЯЕМ ЗАДЕРЖКУ 2 СЕКУНДЫ
    await asyncio.sleep(2)

    # Сообщение с качеством
    quality_text = "Качество заказа – *Обычное*"
    
    # Отправляем сообщение с качеством
    image_path = "images/tutorial/quality_ordinary.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=quality_text
        )
    except Exception as e:
        await callback.message.answer(quality_text)
    
    # Клавиатура для подарка
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    quality_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Подарить холдер", callback_data="holder_gift")]
    ])
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption="Нажмите чтобы подарить картхолдер другу",
            reply_markup=quality_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            "Нажмите чтобы подарить картхолдер другу",
            reply_markup=quality_keyboard
        )
    
    # Устанавливаем следующее состояние
    await state.set_state(TutorialStates.waiting_for_holder_gift)
    await callback.answer()

# Обработка подарка картхолдера и завершение - Этап 19
@tutorial_router.callback_query(F.data == "holder_gift")
async def holder_gift(callback: CallbackQuery, state: FSMContext):
    """Подарок картхолдера и завершение обучения - Этап 19"""
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Начисляем награду 2000 монет
    progress = tutorial_db.get_tutorial_progress(player_id)
    current_balance = progress[3] if progress else 2000
    new_balance = current_balance + 2000
    tutorial_db.update_player_balance(player_id, new_balance)
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_holder_final")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 19
    stage19_text = (
        "Друг был в восторге и даже заплатил вам 2000 монет за работу. Вы отказывались, понимая какой он кривой, "
        "но друг настоял и отказался забирать их обратно.\n\n"
        "Воодушевлённо таким исходом, вы решили, что теперь проблема с подарками решена навсегда."
    )
    
    # Клавиатура для перехода в магазин (задел для третьей части)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    stage19_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏪 В магазин", callback_data="holder_to_shop")]
    ])
    
    # Отправляем сообщение этапа 19
    image_path = "images/tutorial/holder_final.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage19_text,
            reply_markup=stage19_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage19_text,
            reply_markup=stage19_keyboard
        )
    
    # Устанавливаем финальное состояние
    await state.set_state(TutorialStates.waiting_for_holder_final)
    await callback.answer(f"✅ Получено 2000 монет! Новый баланс: {new_balance}")

# =============================================================================
# ТРЕТЬЯ ЧАСТЬ ОБУЧЕНИЯ - ИЗГОТОВЛЕНИЕ СУМКИ (ЭТАПЫ 20-36)
# =============================================================================

# Обработка кнопки "В магазин" из финала картхолдера - Этап 20
@tutorial_router.callback_query(F.data == "holder_to_shop")
async def holder_to_shop(callback: CallbackQuery, state: FSMContext):
    """Переход в магазин для покупки материалов для сумки - Этап 20"""
    print("🎯 ОТЛАДКА: holder_to_shop вызван - начало третьей части")
    
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_start")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 20
    stage20_text = (
        "Воодушевившись доходом с продажи первого картхолдера, вы решили попробовать сделать что-то посущественнее. "
        "Как раз оставалась кожа на среднюю сумочку.\n\n"
        "Вы посмотрели пару роликов о том, как её сделать, и отправились в магазин за фурнитурой и воском, "
        "чтобы защитить кожу от воды и внешних воздействий."
    )
    
    # Клавиатура для перехода в магазин
    stage20_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить материалы для сумки", callback_data="bag_go_to_shop")]
    ])
    
    # Отправляем сообщение этапа 20
    image_path = "images/tutorial/bag_start.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage20_text,
            reply_markup=stage20_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage20_text,
            reply_markup=stage20_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_start)
    await callback.answer()

# Обработка кнопки "Купить материалы для сумки" - Этап 21
# Обработка кнопки "Купить материалы для сумки" - Этап 21
@tutorial_router.callback_query(F.data == "bag_go_to_shop")
async def bag_go_to_shop(callback: CallbackQuery, state: FSMContext):
    """Магазин для покупки материалов сумки - Этап 21"""
    print("🎯 ОТЛАДКА: bag_go_to_shop вызван")
    
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "in_shop_bag_materials")
    
    # Получаем баланс
    progress = tutorial_db.get_tutorial_progress(player_id)
    balance = progress[3] if progress else 2000
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 21
    stage21_text = "Для изготовления сумки вам понадобятся фурнитура и воск. Выберите категорию:"
    
    # Клавиатура магазина (ПОЛНЫЙ КАТАЛОГ КАК В ЭТАПЕ 10)
    all_categories = [
        ("🔪 Ножи", "shop_bag_knives"),
        ("🕳️ Пробойники", "shop_bag_punches"), 
        ("🔧 Торцбилы", "shop_bag_edges"),
        ("🧵 Материалы", "shop_bag_materials"),
        ("📎 Фурнитура", "shop_bag_hardware"),
        ("🧶 Нитки", "shop_bag_threads"),
        ("🧪 Химия", "shop_bag_chemistry")
    ]
    
    keyboard_buttons = []
    for category_text, callback_data in all_categories:
        keyboard_buttons.append([InlineKeyboardButton(
            text=category_text, 
            callback_data=callback_data
        )])
    
    # Кнопка "Выйти из магазина"
    keyboard_buttons.append([InlineKeyboardButton(
        text="🚪 Выйти из магазина", 
        callback_data="bag_shop_exit"
    )])
    
    shop_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем сообщение этапа 21
    image_path = "images/tutorial/bag_shop.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"{stage21_text}\n\n💰 Ваш баланс: {balance} монет",
            reply_markup=shop_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            f"{stage21_text}\n\n💰 Ваш баланс: {balance} монет",
            reply_markup=shop_keyboard
        )
    
    await state.set_state(TutorialStates.in_shop_bag_materials)
    await state.update_data(player_balance=balance)
    await callback.answer()

# Обработка категорий магазина для сумки
@tutorial_router.callback_query(F.data.startswith("shop_bag_") & ~F.data.in_(["bag_shop_exit"]))
async def show_bag_shop_category(callback: CallbackQuery, state: FSMContext):
    """Показ категорий товаров для сумки"""
    print(f"🎯 ОТЛАДКА: show_bag_shop_category вызван с {callback.data}")
    
    category_map = {
        "shop_bag_knives": "Ножи",
        "shop_bag_punches": "Пробойники", 
        "shop_bag_edges": "Торцбилы",
        "shop_bag_materials": "Материалы",
        "shop_bag_hardware": "Фурнитура",
        "shop_bag_threads": "Нитки",
        "shop_bag_chemistry": "Химия"
    }
    
    category = category_map.get(callback.data)
    if not category:
        await callback.answer("❌ Ошибка категории")
        return
    
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем баланс
    progress = tutorial_db.get_tutorial_progress(player_id)
    balance = progress[3] if progress else 2000
    
    # Получаем ВСЕ товары категории из БД
    all_category_items = tutorial_db.get_shop_items_by_category(category)
    
    # СПИСОК РАЗРЕШЕННЫХ ТОВАРОВ ДЛЯ СУМКИ (этап 21)
    ALLOWED_ITEMS_STAGE_21 = [
        "Дешевая фурнитура для сумок",  # категория "Фурнитура"
        "Пчелиный воск"                 # категория "Химия"
    ]
    
    # Создаем клавиатуру со ВСЕМИ товарами, но с разными callback_data
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    for item in all_category_items:
        item_name = item[0]
        item_price = item[1]
        
        can_afford = balance >= item_price
        is_allowed = item_name in ALLOWED_ITEMS_STAGE_21
        
        item_text = f"{item_name} - {item_price} монет"
        
        if not can_afford:
            item_text += " ❌"
        elif not is_allowed:
            item_text += " 🔒"
        
        # Определяем callback_data в зависимости от доступности
        if not is_allowed:
            # Товар не разрешен для покупки
            callback_data = "not_needed"
        elif not can_afford:
            # Не хватает денег
            callback_data = "cant_afford"
        else:
            if item_name == "Дешевая фурнитура для сумок":
                callback_data = "buy_bag_cheap_bags_hardware"
            elif item_name == "Пчелиный воск":
                callback_data = "buy_bag_beeswax"
            else:
                # Для других товаров (на всякий случай)
                short_name = item_name.lower().replace(' ', '_')[:20]
                callback_data = f"buy_bag_{short_name}"
        
        builder.button(
            text=item_text,
            callback_data=callback_data
        )
    
    
    builder.button(text="🔙 Назад", callback_data="back_to_bag_shop_menu")
    builder.adjust(1)
    keyboard = builder.as_markup()
    
    # Обновляем сообщение
    try:
        await callback.message.edit_caption(
            caption=f"🏪 Магазин - {category}\n\n💰 Ваш баланс: {balance} монет\n📋 Все товары (🔒 - сейчас не нужны):\nВыберите товар:",
            reply_markup=keyboard
        )
        print(f"✅ Категория {category} обновлена")
    except Exception as e:
        print(f"❌ Ошибка обновления категории: {e}")
        await callback.answer("❌ Ошибка обновления")
        return
    
    await state.update_data(current_category=category, player_balance=balance)
    await callback.answer()

# Обработка покупки товаров для сумки - ДОБАВИТЬ ЭТОТ КОД
@tutorial_router.callback_query(F.data.startswith("buy_bag_"))
async def buy_bag_item(callback: CallbackQuery, state: FSMContext):
    """Покупка товаров для сумки"""
    print(f"🎯 ОТЛАДКА: buy_bag_item вызван с {callback.data}")
    
    try:
        data = await state.get_data()
        player_id = data.get('player_id')
        current_category = data.get('current_category', '')
        
        if not player_id:
            await callback.answer("❌ Ошибка: персонаж не найден")
            return
        
        # Получаем callback_data
        callback_data = callback.data.replace("buy_bag_", "")
        print(f"🛒 ОТЛАДКА: Callback_data товара: '{callback_data}'")
        
        # Получаем текущий баланс
        progress = tutorial_db.get_tutorial_progress(player_id)
        balance = progress[3] if progress else 2000
        
        # Получаем ВСЕ товары категории
        all_category_items = tutorial_db.get_shop_items_by_category(current_category)
        print(f"📦 ОТЛАДКА: Все товары в категории {current_category}:")
        for item in all_category_items:
            print(f"  - {item[0]}")
        
        # Прямое сопоставление callback_data с полными названиями
        callback_to_item_map = {
            "cheap_bags_hardware": "Дешевая фурнитура для сумок",
            "beeswax": "Пчелиный воск"
        }
        
        # Ищем товар по полному названию
        full_item_name = callback_to_item_map.get(callback_data)
        item_info = None
        
        if full_item_name:
            for item in all_category_items:
                if item[0] == full_item_name:
                    item_info = item
                    break
        
        if not item_info:
            print(f"❌ Товар не найден: {callback_data}")
            await callback.answer("❌ Товар не найден")
            return
        
        item_name = item_info[0]
        item_price = item_info[1]
        
        print(f"✅ Найден товар: {item_name} за {item_price} монет")
        
        # Проверяем баланс
        if balance < item_price:
            await callback.answer("❌ Недостаточно монет!")
            return
        
        # Проверяем инвентарь на дубликаты
        inventory = tutorial_db.get_tutorial_inventory(player_id)
        for inv_item in inventory:
            if len(inv_item) > 0 and inv_item[0] == item_name:
                await callback.answer("❌ У тебя уже есть этот предмет!")
                return
        
        # Выполняем покупку
        new_balance = balance - item_price
        success = tutorial_db.add_to_tutorial_inventory(player_id, item_name, current_category)
        
        if success:
            # Обновляем баланс
            tutorial_db.update_player_balance(player_id, new_balance)
            
            # Обновляем сообщение магазина
            await back_to_bag_shop_menu(callback, state)
            
            await state.update_data(player_balance=new_balance)
            await callback.answer(f"✅ Куплено: {item_name}")
            print(f"✅ Успешная покупка: {item_name}")
        else:
            await callback.answer("❌ Ошибка при покупке")
            print(f"❌ Ошибка при добавлении в инвентарь: {item_name}")
            
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА в buy_bag_item: {str(e)}")
        import traceback
        traceback.print_exc()
        await callback.answer("❌ Ошибка при покупке")

# Обработка кнопки "Назад" в магазине сумки
@tutorial_router.callback_query(F.data == "back_to_bag_shop_menu")
async def back_to_bag_shop_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню магазина сумки"""
    print("🎯 ОТЛАДКА: back_to_bag_shop_menu вызван")
    
    try:
        data = await state.get_data()
        player_id = data.get('player_id')
        
        progress = tutorial_db.get_tutorial_progress(player_id)
        balance = progress[3] if progress else 2000
        
        # Полный каталог категорий
        all_categories = [
            ("🔪 Ножи", "shop_bag_knives"),
            ("🕳️ Пробойники", "shop_bag_punches"), 
            ("🔧 Торцбилы", "shop_bag_edges"),
            ("🧵 Материалы", "shop_bag_materials"),
            ("📎 Фурнитура", "shop_bag_hardware"),
            ("🧶 Нитки", "shop_bag_threads"),
            ("🧪 Химия", "shop_bag_chemistry")
        ]
        
        keyboard_buttons = []
        for category_text, callback_data in all_categories:
            keyboard_buttons.append([InlineKeyboardButton(
                text=category_text, 
                callback_data=callback_data
            )])
        
        # Кнопка "Выйти из магазина"
        keyboard_buttons.append([InlineKeyboardButton(
            text="🚪 Выйти из магазина", 
            callback_data="bag_shop_exit"
        )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_caption(
            caption=f"Для изготовления сумки вам понадобятся фурнитура и воск. Выберите категорию:\n\n💰 Ваш баланс: {balance} монет",
            reply_markup=keyboard
        )
        
        print("✅ Успешный возврат в главное меню магазина сумки")
        await callback.answer()
        
    except Exception as e:
        print(f"❌ Ошибка в back_to_bag_shop_menu: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

# Обработка кнопки "Выйти из магазина" для сумки - Этап 21
@tutorial_router.callback_query(F.data == "bag_shop_exit")
async def bag_shop_exit(callback: CallbackQuery, state: FSMContext):
    """Выход из магазина с проверкой покупок - Этап 21"""
    print("🎯 ОТЛАДКА: bag_shop_exit вызван")
    
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем инвентарь игрока
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    inventory_items = [item[0] for item in inventory]
    
    # Обязательные товары для этапа 21
    required_items = ["Дешевая фурнитура для сумок", "Пчелиный воск"]
    
    # Проверяем, какие товары отсутствуют
    missing_items = []
    for item in required_items:
        if item not in inventory_items:
            missing_items.append(item)
    
    print(f"🎒 ОТЛАДКА: Проверка инвентаря для выхода: {inventory_items}")
    print(f"❌ Отсутствующие товары: {missing_items}")
    
    # Если есть отсутствующие товары - не пускаем
    if missing_items:
        missing_text = "\n• " + "\n• ".join(missing_items)
        await callback.answer(
            f"❌ Ты еще не все купил!\n\nНе хватает:{missing_text}\n\nВернись и докупи необходимые товары.",
            show_alert=True
        )
        return
    
    # Все товары куплены - можно выходить
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_materials_selection")
    
    # Редактируем сообщение магазина
    await callback.message.edit_caption(
        caption="🏪 Спасибо за покупку! Возвращайтесь еще!",
        reply_markup=None
    )
    
    await callback.answer()
    
    # Переход к этапу 22
    await bag_go_home(callback, state)

# Обработка кнопки "Вернуться домой" - Этап 22
@tutorial_router.callback_query(F.data == "bag_go_home")
async def bag_go_home(callback: CallbackQuery, state: FSMContext):
    """Начало мини-игры изготовления сумки - Этап 22"""
    print("🎯 ОТЛАДКА: bag_go_home вызван")
    
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_materials_selection")
    
    # Удаляем кнопки из предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 22
    stage22_text = (
        "Вы с энтузиазмом принялись за работу.\n\n"
        "Выберите материалы из инвентаря:"
    )
    
    # Получаем инвентарь игрока
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    material_items = [item[0] for item in inventory if any(keyword in item[0].lower() for keyword in ["кожа", "фурнитура"])]
    
    # Инициализируем список выбранных материалов
    await state.update_data(selected_bag_materials=[])
    
    # Создаем клавиатуру выбора материалов
    keyboard_buttons = []
    for item_name in material_items:
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🔘 {item_name}", 
            callback_data=f"toggle_bag_material_{item_name.replace(' ', '_')}"
        )])
    
    # Кнопка продолжения
    keyboard_buttons.append([InlineKeyboardButton(
        text="⏭️ Продолжить (выберите материалы)", 
        callback_data="bag_materials_not_selected"
    )])
    
    materials_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем сообщение этапа 22
    image_path = "images/tutorial/bag_materials.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage22_text,
            reply_markup=materials_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage22_text,
            reply_markup=materials_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_materials_selection)
    await callback.answer()

# Обработка toggle выбора материалов для сумки - Этап 22
@tutorial_router.callback_query(F.data.startswith("toggle_bag_material_"))
async def toggle_bag_material_selection(callback: CallbackQuery, state: FSMContext):
    """Toggle выбор материалов для сумки"""
    data = await state.get_data()
    player_id = data.get('player_id')
    selected_materials = data.get('selected_bag_materials', [])
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем название материала
    material_name = callback.data.replace("toggle_bag_material_", "").replace("_", " ")
    
    # Toggle выбор материала
    if material_name in selected_materials:
        selected_materials.remove(material_name)
        await callback.answer(f"❌ {material_name} - выбор отменен")
    else:
        selected_materials.append(material_name)
        await callback.answer(f"✅ {material_name} - выбран")
    
    # Сохраняем обновленный список
    await state.update_data(selected_bag_materials=selected_materials)
    
    # Получаем инвентарь для обновления клавиатуры
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    material_items = [item[0] for item in inventory if any(keyword in item[0].lower() for keyword in ["кожа", "фурнитура"])]
    
    # Создаем обновленную клавиатуру
    keyboard_buttons = []
    for item_name in material_items:
        emoji = "✅" if item_name in selected_materials else "🔘"
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"{emoji} {item_name}", 
            callback_data=f"toggle_bag_material_{item_name.replace(' ', '_')}"
        )])
    
    # Проверяем выбранные материалы
    required_materials = ["Кожа для сумок (дешевая)", "Дешевая фурнитура для сумок"]
    all_required_selected = all(material in selected_materials for material in required_materials)
    
    if all_required_selected:
        keyboard_buttons.append([InlineKeyboardButton(
            text="⏭️ Продолжить", 
            callback_data="bag_materials_confirmed"
        )])
    else:
        keyboard_buttons.append([InlineKeyboardButton(
            text="⏭️ Продолжить (выберите материалы)", 
            callback_data="bag_materials_not_selected"
        )])
    
    updated_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Обновляем сообщение
    try:
        await callback.message.edit_reply_markup(reply_markup=updated_keyboard)
    except Exception as e:
        await callback.answer("Обновите сообщение")

# Обработка попытки продолжить без выбора материалов
@tutorial_router.callback_query(F.data == "bag_materials_not_selected")
async def bag_materials_not_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка попытки продолжить без выбора материалов"""
    data = await state.get_data()
    selected_materials = data.get('selected_bag_materials', [])
    
    required_materials = ["Кожа для сумок (дешевая)", "Дешевая фурнитура для сумок"]
    missing_materials = [material for material in required_materials if material not in selected_materials]
    
    if missing_materials:
        missing_text = ", ".join(missing_materials)
        await callback.answer(f"❌ Не выбраны: {missing_text}", show_alert=True)
    else:
        await callback.answer("✅ Все материалы выбраны")

# Обработка подтверждения выбора материалов - Этап 23
@tutorial_router.callback_query(F.data == "bag_materials_confirmed")
async def bag_materials_confirmed(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора материалов - переход к выбору инструментов - Этап 23"""
    data = await state.get_data()
    player_id = data.get('player_id')
    selected_materials = data.get('selected_bag_materials', [])
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Проверяем выбор
    required_materials = ["Кожа для сумок (дешевая)", "Дешевая фурнитура для сумок"]
    if not all(material in selected_materials for material in required_materials):
        await callback.answer("❌ Выберите все необходимые материалы", show_alert=True)
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_tools_selection")
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 23
    stage23_text = (
        "Из ящика для инструментов вы достали...\n\n"
        "Выберите инструменты из инвентаря:"
    )
    
    # Получаем инвентарь игрока
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    tool_items = []
    for item in inventory:
        item_name = item[0]
        if any(keyword in item_name.lower() for keyword in ["нож", "пробойник", "мультитул"]):
            tool_items.append(item_name)
    
    # Инициализируем список выбранных инструментов
    await state.update_data(selected_bag_tools=[])
    
    # Создаем клавиатуру выбора инструментов
    keyboard_buttons = []
    for tool_name in tool_items:
        # Создаем простые callback_data как в картхолдере
        if tool_name == "Канцелярский нож":
            callback_data = "toggle_bag_tool_knife"
        elif tool_name == "Строчные пробойники PFG":
            callback_data = "toggle_bag_tool_punch"
        elif tool_name == "Высечные пробойники":
            callback_data = "toggle_bag_tool_punch_set"
        elif tool_name == "Мультитул 3 в 1":
            callback_data = "toggle_bag_tool_multitool"
        else:
            callback_data = f"toggle_bag_tool_{tool_name.replace(' ', '_').lower()[:15]}"
        
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🔘 {tool_name}", 
            callback_data=callback_data
        )])
    
    # Кнопка продолжения
    keyboard_buttons.append([InlineKeyboardButton(
        text="⏭️ Продолжить (выберите инструменты)", 
        callback_data="bag_tools_not_selected"
    )])
    
    tools_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем сообщение этапа 23
    image_path = "images/tutorial/bag_tools.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage23_text,
            reply_markup=tools_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage23_text,
            reply_markup=tools_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_tools_selection)
    await callback.answer("✅ Материалы выбраны!")

# Обработка toggle выбора инструментов для сумки - Этап 23
@tutorial_router.callback_query(F.data.startswith("toggle_bag_tool_"))
async def toggle_bag_tool_selection(callback: CallbackQuery, state: FSMContext):
    """Toggle выбор инструментов для сумки"""
    data = await state.get_data()
    player_id = data.get('player_id')
    selected_tools = data.get('selected_bag_tools', [])
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем код инструмента и преобразуем в название
    tool_code = callback.data.replace("toggle_bag_tool_", "")
    
    tool_map = {
        "knife": "Канцелярский нож",
        "punch": "Строчные пробойники PFG", 
        "punch_set": "Высечные пробойники",
        "multitool": "Мультитул 3 в 1"
    }
    
    tool_name = tool_map.get(tool_code)
    if not tool_name:
        tool_name = tool_code.replace('_', ' ')
    
    # Toggle выбор инструмента
    if tool_name in selected_tools:
        selected_tools.remove(tool_name)
        await callback.answer(f"❌ {tool_name} - выбор отменен")
    else:
        selected_tools.append(tool_name)
        await callback.answer(f"✅ {tool_name} - выбран")
    
    # Сохраняем обновленный список
    await state.update_data(selected_bag_tools=selected_tools)
    
    # Получаем инвентарь для обновления клавиатуры
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    tool_items = []
    for item in inventory:
        item_name = item[0]
        if any(keyword in item_name.lower() for keyword in ["нож", "пробойник", "мультитул"]):
            tool_items.append(item_name)
    
    # Создаем обновленную клавиатуру
    keyboard_buttons = []
    for tool_name in tool_items:
        emoji = "✅" if tool_name in selected_tools else "🔘"
        
        # Создаем callback_data как при первоначальном создании
        if tool_name == "Канцелярский нож":
            callback_data = "toggle_bag_tool_knife"
        elif tool_name == "Строчные пробойники PFG":
            callback_data = "toggle_bag_tool_punch"
        elif tool_name == "Высечные пробойники":
            callback_data = "toggle_bag_tool_punch_set"
        elif tool_name == "Мультитул 3 в 1":
            callback_data = "toggle_bag_tool_multitool"
        else:
            callback_data = f"toggle_bag_tool_{tool_name.replace(' ', '_').lower()[:15]}"
        
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"{emoji} {tool_name}", 
            callback_data=callback_data
        )])
    
    # Проверяем выбранные инструменты
    required_tools = ["Канцелярский нож", "Строчные пробойники PFG", "Высечные пробойники", "Мультитул 3 в 1"]
    all_required_selected = all(tool in selected_tools for tool in required_tools)
    
    if all_required_selected:
        keyboard_buttons.append([InlineKeyboardButton(
            text="⏭️ Продолжить", 
            callback_data="bag_tools_confirmed"
        )])
    else:
        keyboard_buttons.append([InlineKeyboardButton(
            text="⏭️ Продолжить (выберите инструменты)", 
            callback_data="bag_tools_not_selected"
        )])
    
    updated_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Обновляем сообщение
    try:
        await callback.message.edit_reply_markup(reply_markup=updated_keyboard)
    except Exception as e:
        await callback.answer("Обновите сообщение")

# Обработка попытки продолжить без выбора инструментов
@tutorial_router.callback_query(F.data == "bag_tools_not_selected")
async def bag_tools_not_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка попытки продолжить без выбора инструментов"""
    data = await state.get_data()
    selected_tools = data.get('selected_bag_tools', [])
    
    required_tools = ["Канцелярский нож", "Строчные пробойники PFG", "Высечные пробойники", "Мультитул 3 в 1"]
    missing_tools = [tool for tool in required_tools if tool not in selected_tools]
    
    if missing_tools:
        missing_text = ", ".join(missing_tools)
        await callback.answer(f"❌ Не выбраны: {missing_text}", show_alert=True)
    else:
        await callback.answer("✅ Все инструменты выбраны")

# Обработка подтверждения выбора инструментов - Этап 24
@tutorial_router.callback_query(F.data == "bag_tools_confirmed")
async def bag_tools_confirmed(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора инструментов - переход к обработке кожи - Этап 24"""
    data = await state.get_data()
    player_id = data.get('player_id')
    selected_tools = data.get('selected_bag_tools', [])
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Проверяем выбор
    required_tools = ["Канцелярский нож", "Строчные пробойники PFG", "Высечные пробойники", "Мультитул 3 в 1"]
    if not all(tool in selected_tools for tool in required_tools):
        await callback.answer("❌ Выберите все необходимые инструменты", show_alert=True)
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_wax_selection")
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 24
    stage24_text = (
        "Вы раскроили детали по размерам из видео. Теперь вам нужно обработать кожу, чтобы защитить её от воды.\n\n"
        "Выберите воск из инвентаря:"
    )
    
    # Получаем инвентарь игрока (воск)
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    wax_items = [item[0] for item in inventory if "воск" in item[0].lower()]
    
    # Создаем клавиатуру выбора воска
    keyboard_buttons = []
    for item_name in wax_items:
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🧴 {item_name}", 
            callback_data=f"select_bag_wax_{item_name.replace(' ', '_')}"
        )])
    
    wax_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем сообщение этапа 24
    image_path = "images/tutorial/bag_wax.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage24_text,
            reply_markup=wax_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage24_text,
            reply_markup=wax_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_wax_selection)
    await callback.answer("✅ Инструменты выбраны!")

# Обработка выбора воска - Этап 25
@tutorial_router.callback_query(F.data.startswith("select_bag_wax_"))
async def select_bag_wax(callback: CallbackQuery, state: FSMContext):
    """Выбор воска для обработки кожи - Этап 25"""
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем название воска
    wax_name = callback.data.replace("select_bag_wax_", "").replace("_", " ")
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_threads_selection")
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 25
    stage25_text = (
        "Обработав детали, вы приступаете к сборке.\n\n"
        "Выберите нитки из инвентаря:"
    )
    
    # Получаем инвентарь игрока (нитки)
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    thread_items = [item[0] for item in inventory if "нитки" in item[0].lower()]
    
    # Создаем клавиатуру выбора ниток
    keyboard_buttons = []
    for item_name in thread_items:
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🧵 {item_name}", 
            callback_data=f"select_bag_thread_{item_name.replace(' ', '_')}"
        )])
    
    threads_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем сообщение этапа 25
    image_path = "images/tutorial/bag_threads.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage25_text,
            reply_markup=threads_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage25_text,
            reply_markup=threads_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_threads_selection)
    await callback.answer(f"✅ Выбрано: {wax_name}")

# Обработка выбора ниток - Этап 26
@tutorial_router.callback_query(F.data.startswith("select_bag_thread_"))
async def select_bag_thread(callback: CallbackQuery, state: FSMContext):
    """Выбор ниток для сборки - Этап 26"""
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем название ниток
    thread_name = callback.data.replace("select_bag_thread_", "").replace("_", " ")
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_quality_1")
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 26
    stage26_text = (
        "Около двух вечеров вам понадобилось, чтобы собрать вашу первую сумку. На видео в YouTube всё казалось гораздо проще.\n\n"
        "В реальной жизни всё вышло менее удачно:\n"
        "• Мультитул то и дело драл кожу и не давал сделать ровную фаску\n"
        "• Воск не распределился равномерно по коже, в итоге на сумке остались тёмные, слегка липкие пятна\n"
        "• Шов местами 'гуляет', и стежки лежат неровно, местами как будто перетянуты"
    )
    
    # Клавиатура для оценки результата
    stage26_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Оценить результат", callback_data="bag_evaluate_quality_1")]
    ])
    
    # Отправляем сообщение этапа 26
    image_path = "images/tutorial/bag_result_1.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage26_text,
            reply_markup=stage26_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage26_text,
            reply_markup=stage26_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_quality_1)
    await callback.answer(f"✅ Выбрано: {thread_name}")

# Обработка оценки качества первой попытки - Этап 27
@tutorial_router.callback_query(F.data == "bag_evaluate_quality_1")
async def bag_evaluate_quality_1(callback: CallbackQuery, state: FSMContext):
    """Оценка качества первой попытки сумки - Этап 27"""
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_retry")
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Сообщение с качеством
    quality_text = "Качество заказа – Брак"
    
    # Отправляем сообщение с качеством
    image_path = "images/tutorial/quality_reject.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=quality_text
        )
    except Exception as e:
        await callback.message.answer(quality_text)
    
    # Автоматическое списание материалов
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    for item in inventory:
        if item[0] in ["Кожа для сумок (дешевая)", "Дешевая фурнитура для сумок"]:
            # Удаляем материал из инвентаря
            conn = tutorial_db.get_connection()
            try:
                conn.execute(
                    'DELETE FROM tutorial_inventory WHERE player_id = ? AND item_name = ?',
                    (player_id, item[0])
                )
                conn.commit()
            finally:
                conn.close()
    
    # Ждем 2 секунды
    await asyncio.sleep(2)
    
    # Текст для этапа 28
    stage28_text = (
        "Вы с досадой разглядывали результат. Стало ясно: для такой сложной вещи, как сумка, дешевые материалы — это путь в никуда. "
        "'В следующий раз возьму что-то получше', — твердо решаете вы.\n\n"
        "Благо на днях выдали премию"
    )
    
    # Пополняем баланс на 1000 монет
    progress = tutorial_db.get_tutorial_progress(player_id)
    current_balance = progress[3] if progress else 2000
    new_balance = current_balance + 1000
    tutorial_db.update_player_balance(player_id, new_balance)
    
    # Клавиатура для перехода в магазин
    stage28_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить материалы получше", callback_data="bag_retry_shop")]
    ])
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage28_text,
            reply_markup=stage28_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage28_text,
            reply_markup=stage28_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_retry)
    await state.update_data(player_balance=new_balance)
    await callback.answer(f"✅ Получено 1000 монет! Новый баланс: {new_balance}")

# Обработка кнопки "Купить материалы получше" - Этап 29
@tutorial_router.callback_query(F.data == "bag_retry_shop")
async def bag_retry_shop(callback: CallbackQuery, state: FSMContext):
    """Вторая закупка в магазине - Этап 29"""
    print("🎯 ОТЛАДКА: bag_retry_shop вызван")
    
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "in_shop_bag_retry")
    
    # Получаем баланс
    progress = tutorial_db.get_tutorial_progress(player_id)
    balance = progress[3] if progress else 3000  # +1000 от премии
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 29
    stage29_text = "Для второй попытки выберите качественные материалы:"
    
    # Клавиатура магазина
    allowed_categories = [
        ("🧵 Материалы для сумок", "shop_bag_retry_materials"),
        ("📎 Фурнитура для сумок", "shop_bag_retry_hardware"),
        ("🧶 Нитки", "shop_bag_retry_threads"),
        ("🧪 Химия", "shop_bag_retry_chemistry")
    ]
    
    keyboard_buttons = []
    for category_text, callback_data in allowed_categories:
        keyboard_buttons.append([InlineKeyboardButton(
            text=category_text, 
            callback_data=callback_data
        )])
    
    # Кнопка "Вернуться домой"
    keyboard_buttons.append([InlineKeyboardButton(
        text="🚪 Вернуться домой (купите все материалы)", 
        callback_data="bag_retry_shop_not_ready"
    )])
    
    shop_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем сообщение этапа 29
    image_path = "images/tutorial/bag_retry_shop.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"{stage29_text}\n\n💰 Ваш баланс: {balance} монет",
            reply_markup=shop_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            f"{stage29_text}\n\n💰 Ваш баланс: {balance} монет",
            reply_markup=shop_keyboard
        )
    
    await state.set_state(TutorialStates.in_shop_bag_retry)
    await state.update_data(player_balance=balance)
    await callback.answer()

# Обработка категорий магазина для второй попытки
@tutorial_router.callback_query(F.data.startswith("shop_bag_retry_"))
async def show_bag_retry_shop_category(callback: CallbackQuery, state: FSMContext):
    """Показ категорий товаров для второй попытки"""
    print(f"🎯 ОТЛАДКА: show_bag_retry_shop_category вызван с {callback.data}")
    
    category_map = {
        "shop_bag_retry_materials": "Материалы",
        "shop_bag_retry_hardware": "Фурнитура",
        "shop_bag_retry_threads": "Нитки",
        "shop_bag_retry_chemistry": "Химия"
    }
    
    category = category_map.get(callback.data)
    if not category:
        await callback.answer("❌ Ошибка категории")
        return
    
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем баланс
    progress = tutorial_db.get_tutorial_progress(player_id)
    balance = progress[3] if progress else 3000
    
    # Получаем товары категории
    all_category_items = tutorial_db.get_shop_items_by_category(category)
    
    # Фильтруем только нужные товары для второй попытки
    allowed_items = []
    for item in all_category_items:
        item_name = item[0]
        if category == "Материалы" and "сумок" in item_name.lower() and "средняя" in item_name.lower():
            allowed_items.append(item)
        elif category == "Фурнитура" and "сумок" in item_name.lower() and "средняя" in item_name.lower():
            allowed_items.append(item)
        elif category == "Нитки" and "синтетические" in item_name.lower():
            allowed_items.append(item)
        elif category == "Химия" and "масловосковые" in item_name.lower():
            allowed_items.append(item)
    
    # Создаем клавиатуру
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    if allowed_items:
        for item in allowed_items:
            item_name = item[0]
            item_price = item[1]
            
            can_afford = balance >= item_price
            item_text = f"{item_name} - {item_price} монет"
            
            if not can_afford:
                item_text += " ❌"
            
            callback_data = f"buy_bag_retry_{item_name.replace(' ', '_')}" if can_afford else "cant_afford"
            
            builder.button(
                text=item_text,
                callback_data=callback_data
            )
    else:
        builder.button(
            text="🚫 Нет подходящих товаров",
            callback_data="not_needed"
        )
    
    builder.button(text="🔙 Назад", callback_data="back_to_bag_retry_shop_menu")
    builder.adjust(1)
    keyboard = builder.as_markup()
    
    # Обновляем сообщение
    try:
        await callback.message.edit_caption(
            caption=f"🏪 Магазин - {category}\n\n💰 Ваш баланс: {balance} монет\nВыберите товар:",
            reply_markup=keyboard
        )
    except Exception as e:
        await callback.answer("❌ Ошибка обновления")
        return
    
    await state.update_data(current_category=category, player_balance=balance)
    await callback.answer()

# Обработка кнопки "Назад" в магазине второй попытки
@tutorial_router.callback_query(F.data == "back_to_bag_retry_shop_menu")
async def back_to_bag_retry_shop_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню магазина второй попытки"""
    print("🎯 ОТЛАДКА: back_to_bag_retry_shop_menu вызван")
    
    try:
        data = await state.get_data()
        player_id = data.get('player_id')
        
        progress = tutorial_db.get_tutorial_progress(player_id)
        balance = progress[3] if progress else 3000
        
        # Проверяем инвентарь
        inventory = tutorial_db.get_tutorial_inventory(player_id)
        inventory_items = [item[0] for item in inventory]
        
        # Проверяем куплены ли все нужные товары
        required_items = [
            "Кожа для сумок (средняя)",
            "Средняя фурнитура для сумок", 
            "Синтетические нитки",
            "Масловосковые смеси"
        ]
        has_all_items = all(item in inventory_items for item in required_items)
        
        # Клавиатура магазина
        allowed_categories = [
            ("🧵 Материалы для сумок", "shop_bag_retry_materials"),
            ("📎 Фурнитура для сумок", "shop_bag_retry_hardware"),
            ("🧶 Нитки", "shop_bag_retry_threads"),
            ("🧪 Химия", "shop_bag_retry_chemistry")
        ]
        
        keyboard_buttons = []
        for category_text, callback_data in allowed_categories:
            keyboard_buttons.append([InlineKeyboardButton(
                text=category_text, 
                callback_data=callback_data
            )])
        
        # Кнопка "Вернуться домой"
        if has_all_items:
            keyboard_buttons.append([InlineKeyboardButton(
                text="🚪 Вернуться домой", 
                callback_data="bag_retry_go_home"
            )])
        else:
            keyboard_buttons.append([InlineKeyboardButton(
                text="🚪 Вернуться домой (купите все материалы)", 
                callback_data="bag_retry_shop_not_ready"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_caption(
            caption=f"Для второй попытки выберите качественные материалы:\n\n💰 Ваш баланс: {balance} монет",
            reply_markup=keyboard
        )
        
        await callback.answer()
        
    except Exception as e:
        print(f"❌ Ошибка в back_to_bag_retry_shop_menu: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

# Обработка покупки товаров для второй попытки
@tutorial_router.callback_query(F.data.startswith("buy_bag_retry_"))
async def buy_bag_retry_item(callback: CallbackQuery, state: FSMContext):
    """Покупка товаров для второй попытки сумки"""
    print(f"🎯 ОТЛАДКА: buy_bag_retry_item вызван с {callback.data}")
    
    try:
        data = await state.get_data()
        player_id = data.get('player_id')
        current_category = data.get('current_category', '')
        
        if not player_id:
            await callback.answer("❌ Ошибка: персонаж не найден")
            return
        
        # Получаем название товара
        item_name = callback.data.replace("buy_bag_retry_", "").replace("_", " ")
        
        # Получаем баланс
        progress = tutorial_db.get_tutorial_progress(player_id)
        balance = progress[3] if progress else 3000
        
        # Получаем товары категории
        all_category_items = tutorial_db.get_shop_items_by_category(current_category)
        
        # Ищем товар
        item_info = None
        for item in all_category_items:
            if item[0] == item_name:
                item_info = item
                break
        
        if not item_info:
            await callback.answer("❌ Товар не найден")
            return
        
        item_price = item_info[1]
        
        # Проверяем баланс
        if balance < item_price:
            await callback.answer("❌ Недостаточно монет!")
            return
        
        # Проверяем инвентарь
        inventory = tutorial_db.get_tutorial_inventory(player_id)
        for inv_item in inventory:
            if len(inv_item) > 0 and inv_item[0] == item_name:
                await callback.answer("❌ У тебя уже есть этот предмет!")
                return
        
        # Выполняем покупку
        new_balance = balance - item_price
        success = tutorial_db.add_to_tutorial_inventory(player_id, item_name, current_category)
        
        if success:
            tutorial_db.update_player_balance(player_id, new_balance)
            await back_to_bag_retry_shop_menu(callback, state)
            await callback.answer(f"✅ Куплено: {item_name}")
        else:
            await callback.answer("❌ Ошибка при покупке")
            
    except Exception as e:
        print(f"❌ Ошибка в buy_bag_retry_item: {e}")
        await callback.answer("❌ Ошибка при покупке")

# Обработка попытки выйти без всех материалов (вторая попытка)
@tutorial_router.callback_query(F.data == "bag_retry_shop_not_ready")
async def bag_retry_shop_not_ready(callback: CallbackQuery, state: FSMContext):
    """Обработка попытки выйти без всех материалов для второй попытки"""
    data = await state.get_data()
    player_id = data.get('player_id')
    
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    inventory_items = [item[0] for item in inventory]
    
    required_items = [
        "Кожа для сумок (средняя)",
        "Средняя фурнитура для сумок",
        "Синтетические нитки", 
        "Масловосковые смеси"
    ]
    missing_items = [item for item in required_items if item not in inventory_items]
    
    if missing_items:
        missing_text = ", ".join(missing_items)
        await callback.answer(f"❌ Не хватает: {missing_text}", show_alert=True)
    else:
        await callback.answer("✅ Все материалы куплены, можно возвращаться домой")

# Обработка кнопки "Вернуться домой" (вторая попытка) - Этап 30
@tutorial_router.callback_query(F.data == "bag_retry_go_home")
async def bag_retry_go_home(callback: CallbackQuery, state: FSMContext):
    """Начало второй мини-игры изготовления сумки - Этап 30"""
    print("🎯 ОТЛАДКА: bag_retry_go_home вызван")
    
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_retry_start")
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 30
    stage30_text = (
        "Вооружившись качественной кожей и фурнитурой, вы чувствуете себя увереннее. "
        "На этот раз вы подошли к делу более обстоятельно: нашли подробный туториал от опытного мастера "
        "и заранее разложили всё необходимое на столе."
    )
    
    # Клавиатура для начала работы
    stage30_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔨 Приступить к работе", callback_data="bag_retry_start")]
    ])
    
    # Отправляем сообщение этапа 30
    image_path = "images/tutorial/bag_retry_start.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage30_text,
            reply_markup=stage30_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage30_text,
            reply_markup=stage30_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_retry_start)
    await callback.answer()

# Обработка кнопки "Приступить к работе" - Этап 31
@tutorial_router.callback_query(F.data == "bag_retry_start")
async def bag_retry_start(callback: CallbackQuery, state: FSMContext):
    """Начало выбора материалов для второй попытки - Этап 31"""
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_retry_materials")
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 31
    stage31_text = (
        "Первым делом нужно выбрать материалы. На этот раз в ваших руках — добротная кожа и надежная фурнитура.\n\n"
        "Выберите материалы из инвентаря:"
    )
    
    # Получаем инвентарь игрока
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    material_items = [item[0] for item in inventory if any(keyword in item[0].lower() for keyword in ["кожа", "фурнитура"])]
    
    # Инициализируем список выбранных материалов
    await state.update_data(selected_bag_retry_materials=[])
    
    # Создаем клавиатуру выбора материалов
    keyboard_buttons = []
    for item_name in material_items:
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🔘 {item_name}", 
            callback_data=f"toggle_bag_retry_material_{item_name.replace(' ', '_')}"
        )])
    
    # Кнопка продолжения
    keyboard_buttons.append([InlineKeyboardButton(
        text="⏭️ Продолжить (выберите материалы)", 
        callback_data="bag_retry_materials_not_selected"
    )])
    
    materials_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем сообщение этапа 31
    image_path = "images/tutorial/bag_retry_materials.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage31_text,
            reply_markup=materials_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage31_text,
            reply_markup=materials_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_retry_materials)
    await callback.answer()

# Обработка toggle выбора материалов для второй попытки - Этап 31
@tutorial_router.callback_query(F.data.startswith("toggle_bag_retry_material_"))
async def toggle_bag_retry_material_selection(callback: CallbackQuery, state: FSMContext):
    """Toggle выбор материалов для второй попытки сумки"""
    data = await state.get_data()
    player_id = data.get('player_id')
    selected_materials = data.get('selected_bag_retry_materials', [])
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем название материала
    material_name = callback.data.replace("toggle_bag_retry_material_", "").replace("_", " ")
    
    # Toggle выбор материала
    if material_name in selected_materials:
        selected_materials.remove(material_name)
        await callback.answer(f"❌ {material_name} - выбор отменен")
    else:
        selected_materials.append(material_name)
        await callback.answer(f"✅ {material_name} - выбран")
    
    # Сохраняем обновленный список
    await state.update_data(selected_bag_retry_materials=selected_materials)
    
    # Получаем инвентарь для обновления клавиатуры
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    material_items = [item[0] for item in inventory if any(keyword in item[0].lower() for keyword in ["кожа", "фурнитура"])]
    
    # Создаем обновленную клавиатуру
    keyboard_buttons = []
    for item_name in material_items:
        emoji = "✅" if item_name in selected_materials else "🔘"
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"{emoji} {item_name}", 
            callback_data=f"toggle_bag_retry_material_{item_name.replace(' ', '_')}"
        )])
    
    # Проверяем выбранные материалы
    required_materials = ["Кожа для сумок (средняя)", "Средняя фурнитура для сумок"]
    all_required_selected = all(material in selected_materials for material in required_materials)
    
    if all_required_selected:
        keyboard_buttons.append([InlineKeyboardButton(
            text="⏭️ Продолжить", 
            callback_data="bag_retry_materials_confirmed"
        )])
    else:
        keyboard_buttons.append([InlineKeyboardButton(
            text="⏭️ Продолжить (выберите материалы)", 
            callback_data="bag_retry_materials_not_selected"
        )])
    
    updated_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Обновляем сообщение
    try:
        await callback.message.edit_reply_markup(reply_markup=updated_keyboard)
    except Exception as e:
        await callback.answer("Обновите сообщение")

# Обработка попытки продолжить без выбора материалов (вторая попытка)
@tutorial_router.callback_query(F.data == "bag_retry_materials_not_selected")
async def bag_retry_materials_not_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка попытки продолжить без выбора материалов для второй попытки"""
    data = await state.get_data()
    selected_materials = data.get('selected_bag_retry_materials', [])
    
    required_materials = ["Кожа для сумок (средняя)", "Средняя фурнитура для сумок"]
    missing_materials = [material for material in required_materials if material not in selected_materials]
    
    if missing_materials:
        missing_text = ", ".join(missing_materials)
        await callback.answer(f"❌ Не выбраны: {missing_text}", show_alert=True)
    else:
        await callback.answer("✅ Все материалы выбраны")

# Обработка подтверждения выбора материалов (вторая попытка) - Этап 32
@tutorial_router.callback_query(F.data == "bag_retry_materials_confirmed")
async def bag_retry_materials_confirmed(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора материалов - переход к выбору инструментов - Этап 32"""
    data = await state.get_data()
    player_id = data.get('player_id')
    selected_materials = data.get('selected_bag_retry_materials', [])
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Проверяем выбор
    required_materials = ["Кожа для сумок (средняя)", "Средняя фурнитура для сумок"]
    if not all(material in selected_materials for material in required_materials):
        await callback.answer("❌ Выберите все необходимые материалы", show_alert=True)
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_retry_tools")
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 32
    stage32_text = (
        "Инструменты те же, но в сочетании с качественными материалами работа пошла иначе.\n\n"
        "Выберите инструменты из инвентаря:"
    )
    
    # Получаем инвентарь игрока
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    tool_items = []
    for item in inventory:
        item_name = item[0]
        if any(keyword in item_name.lower() for keyword in ["нож", "пробойник", "мультитул"]):
            tool_items.append(item_name)
    
    # Инициализируем список выбранных инструментов
    await state.update_data(selected_bag_retry_tools=[])
    
    # Создаем клавиатуру выбора инструментов
    keyboard_buttons = []
    for tool_name in tool_items:
        # Создаем простые callback_data
        if tool_name == "Канцелярский нож":
            callback_data = "toggle_bag_retry_tool_knife"
        elif tool_name == "Строчные пробойники PFG":
            callback_data = "toggle_bag_retry_tool_punch"
        elif tool_name == "Высечные пробойники":
            callback_data = "toggle_bag_retry_tool_punch_set"
        elif tool_name == "Мультитул 3 в 1":
            callback_data = "toggle_bag_retry_tool_multitool"
        else:
            callback_data = f"toggle_bag_retry_tool_{tool_name.replace(' ', '_').lower()[:15]}"
        
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🔘 {tool_name}", 
            callback_data=callback_data
        )])
    
    # Кнопка продолжения
    keyboard_buttons.append([InlineKeyboardButton(
        text="⏭️ Продолжить (выберите инструменты)", 
        callback_data="bag_retry_tools_not_selected"
    )])
    
    tools_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем сообщение этапа 32
    image_path = "images/tutorial/bag_retry_tools.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage32_text,
            reply_markup=tools_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage32_text,
            reply_markup=tools_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_retry_tools)
    await callback.answer("✅ Материалы выбраны!")

# Обработка toggle выбора инструментов для второй попытки - Этап 32
@tutorial_router.callback_query(F.data.startswith("toggle_bag_retry_tool_"))
async def toggle_bag_retry_tool_selection(callback: CallbackQuery, state: FSMContext):
    """Toggle выбор инструментов для второй попытки сумки"""
    data = await state.get_data()
    player_id = data.get('player_id')
    selected_tools = data.get('selected_bag_retry_tools', [])
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем код инструмента и преобразуем в название
    tool_code = callback.data.replace("toggle_bag_retry_tool_", "")
    
    tool_map = {
        "knife": "Канцелярский нож",
        "punch": "Строчные пробойники PFG", 
        "punch_set": "Высечные пробойники",
        "multitool": "Мультитул 3 в 1"
    }
    
    tool_name = tool_map.get(tool_code)
    if not tool_name:
        tool_name = tool_code.replace('_', ' ')
    
    # Toggle выбор инструмента
    if tool_name in selected_tools:
        selected_tools.remove(tool_name)
        await callback.answer(f"❌ {tool_name} - выбор отменен")
    else:
        selected_tools.append(tool_name)
        await callback.answer(f"✅ {tool_name} - выбран")
    
    # Сохраняем обновленный список
    await state.update_data(selected_bag_retry_tools=selected_tools)
    
    # Получаем инвентарь для обновления клавиатуры
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    tool_items = []
    for item in inventory:
        item_name = item[0]
        if any(keyword in item_name.lower() for keyword in ["нож", "пробойник", "мультитул"]):
            tool_items.append(item_name)
    
    # Создаем обновленную клавиатуру
    keyboard_buttons = []
    for tool_name in tool_items:
        emoji = "✅" if tool_name in selected_tools else "🔘"
        
        # Создаем callback_data как при первоначальном создании
        if tool_name == "Канцелярский нож":
            callback_data = "toggle_bag_retry_tool_knife"
        elif tool_name == "Строчные пробойники PFG":
            callback_data = "toggle_bag_retry_tool_punch"
        elif tool_name == "Высечные пробойники":
            callback_data = "toggle_bag_retry_tool_punch_set"
        elif tool_name == "Мультитул 3 в 1":
            callback_data = "toggle_bag_retry_tool_multitool"
        else:
            callback_data = f"toggle_bag_retry_tool_{tool_name.replace(' ', '_').lower()[:15]}"
        
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"{emoji} {tool_name}", 
            callback_data=callback_data
        )])
    
    # Проверяем выбранные инструменты
    required_tools = ["Канцелярский нож", "Строчные пробойники PFG", "Высечные пробойники", "Мультитул 3 в 1"]
    all_required_selected = all(tool in selected_tools for tool in required_tools)
    
    if all_required_selected:
        keyboard_buttons.append([InlineKeyboardButton(
            text="⏭️ Продолжить", 
            callback_data="bag_retry_tools_confirmed"
        )])
    else:
        keyboard_buttons.append([InlineKeyboardButton(
            text="⏭️ Продолжить (выберите инструменты)", 
            callback_data="bag_retry_tools_not_selected"
        )])
    
    updated_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Обновляем сообщение
    try:
        await callback.message.edit_reply_markup(reply_markup=updated_keyboard)
    except Exception as e:
        await callback.answer("Обновите сообщение")

# Обработка попытки продолжить без выбора инструментов (вторая попытка)
@tutorial_router.callback_query(F.data == "bag_retry_tools_not_selected")
async def bag_retry_tools_not_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка попытки продолжить без выбора инструментов для второй попытки"""
    data = await state.get_data()
    selected_tools = data.get('selected_bag_retry_tools', [])
    
    required_tools = ["Канцелярский нож", "Строчные пробойники PFG", "Высечные пробойники", "Мультитул 3 в 1"]
    missing_tools = [tool for tool in required_tools if tool not in selected_tools]
    
    if missing_tools:
        missing_text = ", ".join(missing_tools)
        await callback.answer(f"❌ Не выбраны: {missing_text}", show_alert=True)
    else:
        await callback.answer("✅ Все инструменты выбраны")

# Обработка подтверждения выбора инструментов (вторая попытка) - Этап 33
@tutorial_router.callback_query(F.data == "bag_retry_tools_confirmed")
async def bag_retry_tools_confirmed(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора инструментов - переход к обработке кожи - Этап 33"""
    data = await state.get_data()
    player_id = data.get('player_id')
    selected_tools = data.get('selected_bag_retry_tools', [])
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Проверяем выбор
    required_tools = ["Канцелярский нож", "Строчные пробойники PFG", "Высечные пробойники", "Мультитул 3 в 1"]
    if not all(tool in selected_tools for tool in required_tools):
        await callback.answer("❌ Выберите все необходимые инструменты", show_alert=True)
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_retry_wax")
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 33
    stage33_text = (
        "Вам показалось, что хорошую кожу даже кроить легче. Она не такая сухая, текстура у неё более ровная, "
        "и на ней меньше точек и царапин.\n\n"
        "Теперь — важный этап защиты от воды. Масловосковая смесь имеет пастообразную текстуру и легче наносится на кожу. "
        "В отличие от воска, её не нужно топить и тереть шерстяной тряпочкой.\n\n"
        "Выберите масловосковую смесь из инвентаря:"
    )
    
    # Получаем инвентарь игрока (масловосковые смеси)
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    wax_items = [item[0] for item in inventory if "масловосковые" in item[0].lower()]
    
    # Создаем клавиатуру выбора
    keyboard_buttons = []
    for item_name in wax_items:
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🧴 {item_name}", 
            callback_data=f"select_bag_retry_wax_{item_name.replace(' ', '_')}"
        )])
    
    wax_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем сообщение этапа 33
    image_path = "images/tutorial/bag_retry_wax.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage33_text,
            reply_markup=wax_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage33_text,
            reply_markup=wax_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_retry_wax)
    await callback.answer("✅ Инструменты выбраны!")

# Обработка выбора масловосковой смеси - Этап 34
@tutorial_router.callback_query(F.data.startswith("select_bag_retry_wax_"))
async def select_bag_retry_wax(callback: CallbackQuery, state: FSMContext):
    """Выбор масловосковой смеси - Этап 34"""
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем название смеси
    wax_name = callback.data.replace("select_bag_retry_wax_", "").replace("_", " ")
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_retry_threads")
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 34
    stage34_text = (
        "Смесь легла ровным, матовым слоем, подчеркивая фактуру кожи и не оставляя липких пятен. Можно приступать к сборке.\n\n"
        "Выберите нитки из инвентаря:"
    )
    
    # Получаем инвентарь игрока (нитки)
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    thread_items = [item[0] for item in inventory if "нитки" in item[0].lower()]
    
    # Создаем клавиатуру выбора ниток
    keyboard_buttons = []
    for item_name in thread_items:
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"🧵 {item_name}", 
            callback_data=f"select_bag_retry_thread_{item_name.replace(' ', '_')}"
        )])
    
    threads_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    # Отправляем сообщение этапа 34
    image_path = "images/tutorial/bag_retry_threads.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage34_text,
            reply_markup=threads_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage34_text,
            reply_markup=threads_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_retry_threads)
    await callback.answer(f"✅ Выбрано: {wax_name}")

# Обработка выбора ниток (вторая попытка) - Этап 35
@tutorial_router.callback_query(F.data.startswith("select_bag_retry_thread_"))
async def select_bag_retry_thread(callback: CallbackQuery, state: FSMContext):
    """Выбор ниток для сборки (вторая попытка) - Этап 35"""
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Получаем название ниток
    thread_name = callback.data.replace("select_bag_retry_thread_", "").replace("_", " ")
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_bag_quality_2")
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Текст для этапа 35
    stage35_text = (
        "На крой, обработку и сборку у вас ушло пару вечеров.\n\n"
        "• Мультитул оставлял желать лучшего, но с этой кожей было чуть проще\n"
        "• Отверстия под шов пробойники пробивали чётко и чисто\n"
        "• Молния на новой фурнитуре скользила плавно, а кнопки защёлкивались с приятным, тугим щелчком\n"
        "• Синтетическая нить не закручивалась и не завязывалась узлами\n\n"
        "Конечно, до идеала ещё далеко, но в ваших руках теперь вполне себе добротная, крепкая сумка."
    )
    
    # Клавиатура для оценки результата
    stage35_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Оценить результат", callback_data="bag_evaluate_quality_2")]
    ])
    
    # Отправляем сообщение этапа 35
    image_path = "images/tutorial/bag_result_2.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage35_text,
            reply_markup=stage35_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage35_text,
            reply_markup=stage35_keyboard
        )
    
    await state.set_state(TutorialStates.waiting_for_bag_quality_2)
    await callback.answer(f"✅ Выбрано: {thread_name}")

# Обработка оценки качества второй попытки - Этап 36
@tutorial_router.callback_query(F.data == "bag_evaluate_quality_2")
async def bag_evaluate_quality_2(callback: CallbackQuery, state: FSMContext):
    """Оценка качества второй попытки сумки - Этап 36"""
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    # Обновляем прогресс
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_final")
    
    # Удаляем кнопки
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    
    # Рандом 50/50 обычный/отличный
    import random
    quality = "Обычное" if random.random() < 0.5 else "Отличное"
    
    # Сообщение с качеством
    quality_text = f"Качество заказа – {quality}"
    
    # Отправляем сообщение с качеством
    image_path = f"images/tutorial/quality_{quality.lower()}.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=quality_text
        )
    except Exception as e:
        await callback.message.answer(quality_text)
    
    # Автоматическое списание материалов
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    materials_to_remove = [
        "Кожа для сумок (средняя)",
        "Средняя фурнитура для сумок", 
        "Масловосковые смеси"
    ]
    
    for material in materials_to_remove:
        for item in inventory:
            if item[0] == material:
                # Удаляем материал из инвентаря
                conn = tutorial_db.get_connection()
                try:
                    conn.execute(
                        'DELETE FROM tutorial_inventory WHERE player_id = ? AND item_name = ?',
                        (player_id, material)
                    )
                    conn.commit()
                finally:
                    conn.close()
                break
    
    # Ждем 2 секунды
    await asyncio.sleep(2)
    
    # Переход к финалу обучения (этап 37)
    await show_final_menu(callback, state)
    
    await callback.answer()

# Финальное меню обучения - Этап 37
async def show_final_menu(callback: CallbackQuery, state: FSMContext):
    """Финальное меню обучения - Этап 37"""
    data = await state.get_data()
    player_id = data.get('player_id')
    
    # Текст для этапа 37
    stage37_text = (
        "Повесив на плечо новую, сделанную своими руками сумку, вы почувствовали не только гордость, но и уверенность в своих силах. "
        "Ваше хобби перешло на новый уровень.\n\n"
        "К вам стали обращаться знакомые и знакомые ваших знакомых: 'Я слышал, ты классные вещи делаешь! "
        "Сможешь мне кошелёк/ремень/чехол смастерить?'\n\n"
        "Так ваше увлечение незаметно превратилось в маленькую, но гордую «Мастерскую для Души». "
        "Теперь ваша задача — оттачивать мастерство, выполняя заказы и превращая их из 'обычных' в 'отличные'."
    )
    
    # Главное игровое меню
    final_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Принять заказ", callback_data="soon_available")],
        [InlineKeyboardButton(text="🛠️ Мой инвентарь", callback_data="soon_available")],
        [InlineKeyboardButton(text="🏪 Магазин", callback_data="soon_available")],
        [InlineKeyboardButton(text="📊 Мой профиль", callback_data="soon_available")]
    ])
    
    # Отправляем финальное сообщение
    image_path = "images/tutorial/final_menu.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=stage37_text,
            reply_markup=final_keyboard
        )
    except Exception as e:
        await callback.message.answer(
            stage37_text,
            reply_markup=final_keyboard
        )

# Обработка кнопок "скоро станет доступно"
@tutorial_router.callback_query(F.data == "soon_available")
async def soon_available(callback: CallbackQuery):
    """Обработка кнопок которые пока не реализованы"""
    await callback.answer("🔧 Эта функция скоро станет доступна!", show_alert=True)


# Обработка нажатия на заблокированные товары
@tutorial_router.callback_query(F.data == "not_available")
async def not_available(callback: CallbackQuery):
    await callback.answer("❌ Пока не могу себе позволить", show_alert=True)

@tutorial_router.callback_query(F.data == "cant_afford")
async def cant_afford(callback: CallbackQuery):
    await callback.answer("❌ Недостаточно денег для покупки!", show_alert=True)

@tutorial_router.callback_query(F.data == "not_in_tutorial")
async def not_in_tutorial(callback: CallbackQuery):
    await callback.answer("❌ Сейчас я не могу себе позволить", show_alert=True)

# Начало обучения
@tutorial_router.callback_query(F.data == "start_tutorial")
async def start_tutorial(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    
    # Получаем активного персонажа
    active_player = db.get_active_player(user_id)
    if not active_player:
        await callback.answer("❌ Ошибка: персонаж не найден")
        return
    
    player_id = active_player[0]  # ID персонажа
    
    # Инициализируем прогресс обучения для этого персонажа
    tutorial_db.init_tutorial_progress(player_id)
    tutorial_db.init_shop_items()
    
    # Удаляем кнопки из предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # СРАЗУ переходим к входу в магазин (показываем описание магазина)
    await enter_shop(callback, state)
    
    await state.set_state(TutorialStates.waiting_for_shop_enter)
    await state.update_data(player_id=player_id, player_balance=2000)
    await callback.answer()

# Обработка входа в магазин
@tutorial_router.callback_query(F.data == "enter_shop")
async def enter_shop(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    player_id = data.get('player_id')

    await state.set_state(TutorialStates.waiting_for_approach)
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_approach")
    
    active_player = db.get_active_player(callback.from_user.id)
    player_name = active_player[2] if active_player else "Игрок"
    
    # Удаляем кнопки из предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Пытаемся отправить картинку магазина
    image_path = "images/tutorial/shop_entrance.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"Войдя в магазин вы видете вдоль стен кожи, подвешенные на крючок. С другой стороны, были стеллажи, на которых кожа лежала в рулонах. Отдельно в углу были витрины с какими-то причудливыми инструментами. Похожие вы видели на Youtube, но эти отличалась.\n\nПобродя по магазину, вы поняли, что вообще не понимаете с чего начать и что выбрать. Десятки разных кож. Цветные и не цветные, мягкие и плотные, гладкие и с текстурой, а выбрать нечего. Девушки-сотрудницы, бегали, мимо и вы уже решил прийти в другой раз.\n\nНо тут вы увидели мужичка, который что-то бойко рассказывал одному из посетителей. Вы решили подойти поближе и послушать.",
            reply_markup=get_approach_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            f"Войдя в магазин вы видете вдоль стен кожи, подвешенные на крючок. С другой стороны, были стеллажи, на которых кожа лежала в рулонах. Отдельно в углу были витрины с какими-то причудливыми инструментами. Похожие вы видели на Youtube, но эти отличалась.\n\nПобродя по магазину, вы поняли, что вообще не понимаете с чего начать и что выбрать. Десятки разных кож. Цветные и не цветные, мягкие и плотные, гладкие и с текстурой, а выбрать нечего. Девушки-сотрудницы, бегали, мимо и вы уже решил прийти в другой раз.\n\nНо тут вы увидели мужичка, который что-то бойко рассказывал одному из посетителей. Вы решили подойти поближе и послушать.",
            reply_markup=get_approach_keyboard()
        )
    
    await state.set_state(TutorialStates.waiting_for_approach)
    tutorial_db.update_tutorial_progress(data.get('player_id'), "waiting_for_approach")
    await callback.answer()

# Обработка подхода поближе
@tutorial_router.callback_query(F.data == "approach_closer")
async def approach_closer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    player_id = data.get('player_id')
    
    await state.set_state(TutorialStates.waiting_for_oldman_approach)
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_oldman_approach")

    active_player = db.get_active_player(callback.from_user.id)
    player_name = active_player[2] if active_player else "Игрок"
    
    # Удаляем кнопки из предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Пытаемся отправить картинку
    image_path = "images/tutorial/oldman_talking.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"Встав в паре шагов, вы стали слушать, делая вид, что что-то выбираете. Мужичок очень увлеченно рассказывал, как он обрабатывает края кошелька. Что-то про то, что у него КМС, правда вы так и не поняли по какому виду спорта. И какой-то сликер.\n\nБуквально через минуту, его собеседник убежал, а вы решили, поросите у мужичка совет с чего начать.",
            reply_markup=get_oldman_approach_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            f"Встав в паре шагов, вы стали слушать, делая вид, что что-то выбираете. Мужичок очень увлеченно рассказывал, как он обрабатывает края кошелька. Что-то про то, что у него КМС, правда вы так и не поняли по какому виду спорта. И какой-то сликер.\n\nБуквально через минуту, его собеседник убежал, а вы решили, поросите у мужичка совет с чего начать.",
            reply_markup=get_oldman_approach_keyboard()
        )
    
    await state.set_state(TutorialStates.waiting_for_oldman_approach)
    tutorial_db.update_tutorial_progress(data.get('player_id'), "waiting_for_oldman_approach")
    await callback.answer()

# Обработка подхода к Гене
@tutorial_router.callback_query(F.data == "approach_oldman")
async def approach_oldman(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    player_id = data.get('player_id')
    
    await state.set_state(TutorialStates.waiting_for_showcase)
    tutorial_db.update_tutorial_progress(player_id, "waiting_for_showcase")
    
    active_player = db.get_active_player(callback.from_user.id)
    player_name = active_player[2] if active_player else "Игрок"
    
    # Удаляем кнопки из предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Первое сообщение без кнопок
    image_path = "images/tutorial/oldman_close.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"Вы подошли, поздоровались и попросили помочь с выбором первых инструментов и кожи"
        )
    except Exception as e:
        await callback.message.answer(
            f"Вы подошли, поздоровались и попросили помочь с выбором первых инструментов и кожи"
        )
    
    # Ждем 3 секунды и отправляем второе сообщение с кнопкой
    await asyncio.sleep(3)
    
    image_path = "images/tutorial/shop_showcase.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"Ну здарова! Меня Геннадием Борисовичем звать. Но зови меня просто Гена. Давай по порядку. Говоришь ремень себе хочешь сделать?\n\nТогда смотри. Много инструментов тебе не надо: нож, пробойник, молоток, торцбил, сликер и отвертка, которой винтики закрутишь. Сколько у тебя денег? Ух, не много. Придется поскромнее прикупить. Я-то уже давно занимаюсь, у меня профессиональные инструменты от Wuta. Не знаешь? Ну когда-нибудь дорастешь.\n\n(продолжая рассказывать, что-то Геннадий Борисович отвел вас к витрине с инструментами)",
            reply_markup=get_showcase_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            f"Ну здарова! Меня Геннадием Борисовичем звать. Но зови меня просто Гена. Давай по порядку. Говоришь ремень себе хочешь сделать?\n\nТогда смотри. Много инструментов тебе не надо: нож, пробойник, молоток, торцбил, сликер и отвертка, которой винтики закрутишь. Сколько у тебя денег? Ух, не много. Придется поскромнее прикупить. Я-то уже давно занимаюсь, у меня профессиональные инструменты от Wuta. Не знаешь? Ну когда-нибудь дорастешь.\n\n(продолжая рассказывать, что-то Геннадий Борисович отвел вас к витрине с инструментами)",
            reply_markup=get_showcase_keyboard()
        )
    
    await state.set_state(TutorialStates.waiting_for_showcase)
    tutorial_db.update_tutorial_progress(data.get('player_id'), "waiting_for_showcase")
    await callback.answer()

# Обработка просмотра витрины
@tutorial_router.callback_query(F.data == "view_showcase")
async def view_showcase(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    player_id = data.get('player_id')

    await state.set_state(TutorialStates.in_shop_menu)
    tutorial_db.update_tutorial_progress(player_id, "in_shop_menu")
    
    active_player = db.get_active_player(callback.from_user.id)
    player_name = active_player[2] if active_player else "Игрок"
    
    # Получаем баланс из БД
    progress = tutorial_db.get_tutorial_progress(player_id)
    balance = progress[3] if progress else 2000  # player_balance
    
    # Удаляем кнопки из предыдущего сообщения
    await callback.message.edit_reply_markup(reply_markup=None)
    
    # Пытаемся отправить картинку витрины
    image_path = "images/tutorial/tools_showcase.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"Вы рассматриваете витрину, узнавая некоторые инструменты, которые видели на Youtube. Они были меньше, чем казалось.\n\nБыли там инструменты и дешевые, и очень дорогие, как буд-то из золота. Например, рядом друг с другом лежала штука похожая на вилку за 400 монет и за 20 000 монет. Без понятия в чем разница.\n\n- Давай соберем тебе набор: выбирай пока самые дешевые, на больше у тебя денег не хватит.\nБери: нож, высечной пробойник, торцбил, сликер. По материалам: ременную ленту дешёвую, пряжку из нержавейки и КМЦ клей. Должно хватить\n\n💰 Ваш текущий баланс: {balance} монет",
            reply_markup=get_shop_menu_keyboard(balance)
        )
    except Exception as e:
        await callback.message.answer(
            f"Вы рассматриваете витрину, узнавая некоторые инструменты, которые видели на Youtube. Они были меньше, чем казалось.\n\nБыли там инструменты и дешевые, и очень дорогие, как буд-то из золота. Например, рядом друг с другом лежала штука похожая на вилку за 400 монет и за 20 000 монет. Без понятия в чем разница.\n\n- Давай соберем тебе набор: выбирай пока самые дешевые, на больше у тебя денег не хватит.\nБери: нож, высечной пробойник, торцбил, сликер. По материалам: ременную ленту дешёвую, пряжку из нержавейки и КМЦ клей. Должно хватить\n\n💰 Ваш текущий баланс: {balance} монет",
            reply_markup=get_shop_menu_keyboard(balance)
        )
    
    await state.set_state(TutorialStates.in_shop_menu)
    tutorial_db.update_tutorial_progress(data.get('player_id'), "in_shop_menu")
    await state.update_data(player_balance=balance)
    await callback.answer()

# Обработчик кнопки "Назад" в магазине
@tutorial_router.callback_query(F.data == "back_to_shop_menu")
async def back_to_shop_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню магазина"""
    try:
        # Получаем данные игрока
        data = await state.get_data()
        player_id = data.get('player_id')
        
        progress = tutorial_db.get_tutorial_progress(player_id)
        balance = progress[3] if progress else 2000
        
        # Создаем клавиатуру главного меню магазина
        keyboard = get_shop_menu_keyboard(balance)
        
        await callback.message.edit_caption(
            caption=f"🏪 Магазин инструментов\n\n💰 Ваш баланс: {balance} монет\nВыберите категорию:",
            reply_markup=keyboard
        )
        
        await state.set_state(TutorialStates.in_shop_menu)
        await callback.answer()
        
    except Exception as e:
        print(f"❌ Ошибка в back_to_shop_menu: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

# Обработка выхода из магазина (проверка инвентаря) - ОБНОВЛЕННАЯ
@tutorial_router.callback_query(F.data == "shop_exit")
async def shop_exit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    player_id = data.get('player_id')
    
    if not player_id:
        print("🔄 player_id не найден в состоянии, получаем из БД...")
        active_player = db.get_active_player(callback.from_user.id)
        if active_player:
            player_id = active_player[0]
            await state.update_data(player_id=player_id)
            print(f"✅ player_id получен из БД: {player_id}")
        else:
            print("❌ Не удалось получить player_id из БД")
            await callback.answer("❌ Ошибка: персонаж не найден")
            return
    # Получаем инвентарь игрока
    inventory = tutorial_db.get_tutorial_inventory(player_id)
    inventory_items = [item[0] for item in inventory]  # список названий товаров
    
    print(f"🎒 ПРОВЕРКА ИНВЕНТАРЯ ПРИ ВЫХОДЕ: {inventory_items}")
    
    # Обязательные товары по сценарию
    required_items = [
        "Канцелярский нож",
        "Высечные пробойники", 
        "Мультитул 3 в 1",
        "Дешевая ременная заготовка",
        "Дешевая фурнитура для ремней"
    ]
    
    # Проверяем, какие товары отсутствуют
    missing_items = []
    for item in required_items:
        if item not in inventory_items:
            missing_items.append(item)
    
    print(f"❌ Отсутствующие товары: {missing_items}")
    
    # Если есть отсутствующие товары - не пускаем
    if missing_items:
        missing_text = "\n• " + "\n• ".join(missing_items)
        await callback.answer(
            f"❌ Ты еще не все купил!\n\nНе хватает:{missing_text}\n\nВернись и докупи необходимые товары.",
            show_alert=True
        )
        return
    
    # Все товары куплены - можно выходить
    # Редактируем сообщение магазина
    await callback.message.edit_caption(
        caption="🏪 Спасибо за покупку, приходите еще!",
        reply_markup=None
    )
    
    await callback.answer()
    
    # Отправляем новое сообщение с текстом про Гену
    active_player = db.get_active_player(callback.from_user.id)
    player_name = active_player[2] if active_player else "Игрок"
    
    image_path = "images/tutorial/exit_shop.jpg"
    if not os.path.exists(image_path):
        image_path = "images/placeholder.jpg"
    
    try:
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
            photo=photo,
            caption=f"Вы вышли из магазина с Геной.\n\n- Ну вроде все что надо купил, вот держи ссылку на одно видео, там парень показывает, как он делает ремень. Не очень профессионально, но Бог с ним. Тебе хватит, чтоб понять, как работать.\n\nПопрощавшись и поблагодарив, вы вернулись домой и решили сразу приняться за работу.",
            reply_markup=get_make_belt_keyboard()
        )
    except Exception as e:
        await callback.message.answer(
            f"Вы вышли из магазина с Геной.\n\n- Ну вроде все что надо купил, вот держи ссылку на одно видео, там парень показывает, как он делает ремень. Не очень профессионально, но Бог с ним. Тебе хватит, чтоб понять, как работать.\n\nПопрощавшись и поблагодарив, вы вернулись домой и решили сразу приняться за работу.",
            reply_markup=get_make_belt_keyboard()
        )
# Обработка категорий магазина
@tutorial_router.callback_query(F.data.startswith("shop_"))
async def show_shop_category(callback: CallbackQuery, state: FSMContext):
    category_map = {
        "shop_knives": "Ножи",
        "shop_punches": "Пробойники", 
        "shop_edges": "Торцбилы",
        "shop_materials": "Материалы",
        "shop_hardware": "Фурнитура"
    }
    
    category = category_map.get(callback.data)
    if not category:
        await callback.answer("❌ Ошибка категории")
        return
    
    print(f"🎯 ОТЛАДКА: Открываем категорию: {category}")
    
    # Получаем товары категории и баланс
    data = await state.get_data()
    player_id = data.get('player_id')
    
    progress = tutorial_db.get_tutorial_progress(player_id)
    balance = progress[3] if progress else 2000
    
    # Получаем ВСЕ товары категории
    all_category_items = tutorial_db.get_shop_items_by_category(category)
    print(f"📦 ОТЛАДКА: Все товары в категории {category}: {all_category_items}")
    
    # СОЗДАЕМ КЛАВИАТУРУ с правильной структурой
    builder = InlineKeyboardBuilder()
    for item in all_category_items:
        try:
            # ПРАВИЛЬНАЯ СТРУКТУРА:
            # item[0] = название (string)
            # item[1] = цена (int) 
            # item[2] = доступность в обучении (0/1)
            item_name = item[0]
            item_price = item[1]
            is_available_in_tutorial = item[2]
            
            print(f"🛒 ОТЛАДКА: Товар - Название: '{item_name}', Цена: {item_price}, Доступен в обучении: {is_available_in_tutorial}")
            
            # Проверяем доступность в обучении
            is_tutorial_item = item_name in AVAILABLE_TUTORIAL_ITEMS.get(category, [])
            
            can_afford = balance >= item_price
            item_text = f"{item_name} - {item_price} монет"
            
            if not can_afford:
                item_text += " ❌"
            elif not is_tutorial_item:
                item_text += " 🔒"
            
            # Определяем callback_data в зависимости от доступности
            if not is_tutorial_item:
                # Товар недоступен в обучении
                callback_data = "not_in_tutorial"
            elif not can_afford:
                # Не хватает денег
                callback_data = "cant_afford"
            else:
                # Можно купить
                callback_data = f"buy_{item_name}"
            
            builder.button(
                text=item_text,
                callback_data=callback_data
            )
        except Exception as e:
            print(f"❌ Ошибка обработки товара {item}: {e}")
            continue
    
    builder.button(text="🔙 Назад", callback_data="back_to_shop_menu")
    builder.adjust(1)
    keyboard = builder.as_markup()
    
    # Обновляем сообщение
    await callback.message.edit_caption(
        caption=f"🏪 Магазин - {category}\n\n"
               f"💰 Ваш баланс: {balance} монет\n"
               f"📋 Все товары (🔒 - недоступны в обучении):\n"
               f"Выберите товар:",
        reply_markup=keyboard
    )
    
    await state.set_state(TutorialStates.in_shop_category)
    await state.update_data(current_category=category, player_balance=balance)
    await callback.answer()

# Обработка покупки товара
@tutorial_router.callback_query(F.data.startswith("buy_"))
async def buy_item(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        player_id = data.get('player_id')
        current_category = data.get('current_category', '')
        
        print(f"🔍 ОТЛАДКА player_id В НАЧАЛЕ: player_id = {player_id}")
        
        # ЕСЛИ player_id НЕТ В СОСТОЯНИИ - ВОССТАНАВЛИВАЕМ
        if not player_id:
            print("🔄 player_id не найден в состоянии, получаем из БД...")
            active_player = db.get_active_player(callback.from_user.id)
            if active_player:
                player_id = active_player[0]
                await state.update_data(player_id=player_id)
                print(f"✅ player_id получен из БД: {player_id}")
            else:
                print("❌ Не удалось получить player_id из БД")
                await callback.answer("❌ Ошибка: персонаж не найден")
                return
        
        # Двойная проверка
        if not player_id:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: player_id is None или 0!")
            await callback.answer("❌ Ошибка: персонаж не найден")
            return
        
        # Получаем название товара из callback_data
        item_name = callback.data.replace("buy_", "")
        print(f"🛒 ПОКУПКА: Начало покупки товара: '{item_name}' для player_id: {player_id}")
        
        # ДАЛЕЕ ИДЕТ СТАРЫЙ КОД (без изменений)...
        # Получаем текущий баланс из БД
        progress = tutorial_db.get_tutorial_progress(player_id)
        balance = progress[3] if progress else 2000
            
        print(f"💰 ПОКУПКА: Баланс игрока {player_id}: {balance}")
        
        # Получаем информацию о товаре
        all_category_items = tutorial_db.get_shop_items_by_category(current_category)
        item_info = None
        
        for item in all_category_items:
            # Сравниваем по названию (item[0])
            if item[0] == item_name:  
                item_info = item
                break
        
        if not item_info:
            print(f"❌ ПОКУПКА: Товар '{item_name}' не найден")
            await callback.answer("❌ Товар не найден")
            return
        
        # Извлекаем данные из кортежа
        item_name = item_info[0]
        item_price = item_info[1]
        is_available_in_tutorial = item_info[2]
        
        print(f"✅ ПОКУПКА: Найден товар: '{item_name}' за {item_price} монет")
        
        # Проверяем, доступен ли товар в обучении
        if item_name not in AVAILABLE_TUTORIAL_ITEMS.get(current_category, []):
            print(f"❌ ПОКУПКА: Товар недоступен в обучении")
            await callback.answer("❌ Этот товар недоступен в обучении!")
            return
        
        # Проверяем баланс
        if balance < item_price:
            print(f"❌ ПОКУПКА: Недостаточно средств. Нужно: {item_price}, есть: {balance}")
            await callback.answer("❌ Недостаточно монет!")
            return
        
        # Проверяем инвентарь
        inventory = tutorial_db.get_tutorial_inventory(player_id)
        print(f"🎒 ПОКУПКА: Текущий инвентарь: {inventory}")
        
        # Проверяем, есть ли уже такой товар в инвентаре (по названию)
        for inv_item in inventory:
            if len(inv_item) > 1 and inv_item[1] == item_name:  # inv_item[1] - название товара в инвентаре
                print(f"❌ ПОКУПКА: Товар уже есть в инвентаре")
                await callback.answer("❌ У тебя уже есть этот предмет!")
                return
        
        # Выполняем покупку
        new_balance = balance - item_price
        print(f"💸 ПОКУПКА: Списание {item_price} монет. Новый баланс: {new_balance}")
        
        # Добавляем в инвентарь (передаем название вместо ID)
        success = tutorial_db.add_to_tutorial_inventory(player_id, item_name, current_category)
        
        if success:
            # Обновляем баланс
            tutorial_db.update_player_balance(player_id, new_balance)
            
            print(f"✅ ПОКУПКА: Успешно! Товар добавлен в инвентарь")
            
            # Обновляем сообщение магазина
            await update_shop_category_message(callback, current_category, new_balance, f"✅ Куплено: {item_name}")
            
            await state.update_data(player_balance=new_balance)
            await callback.answer(f"✅ Куплено: {item_name}")
        else:
            print(f"❌ ПОКУПКА: Ошибка при добавлении в инвентарь")
            await callback.answer("❌ Это я уже купил")
            
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА в buy_item: {str(e)}")
        import traceback
        traceback.print_exc()
        await callback.answer("❌ Я уже это купил")

# Вспомогательная функция для обновления сообщения магазина
async def update_shop_category_message(callback: CallbackQuery, category: str, balance: int, status_message: str = ""):
    """Обновляет сообщение категории магазина"""
    all_category_items = tutorial_db.get_shop_items_by_category(category)
    
    builder = InlineKeyboardBuilder()
    for item in all_category_items:
        item_name = item[0]
        item_price = item[1]
        is_available_in_tutorial = item[2]
        
        # Проверяем доступность в обучении
        is_tutorial_item = item_name in AVAILABLE_TUTORIAL_ITEMS.get(category, [])
        
        can_afford = balance >= item_price
        item_text = f"{item_name} - {item_price} монет"
        
        if not can_afford:
            item_text += " ❌"
        elif not is_tutorial_item:
            item_text += " 🔒"
        
        # Определяем callback_data в зависимости от доступности
        if not is_tutorial_item:
            callback_data = "not_in_tutorial"
        elif not can_afford:
            callback_data = "cant_afford"
        else:
            callback_data = f"buy_{item_name}"
        
        builder.button(
            text=item_text,
            callback_data=callback_data
        )
    
    builder.button(text="🔙 Назад", callback_data="back_to_shop_menu")
    builder.adjust(1)
    keyboard = builder.as_markup()
    
    caption = f"🏪 Магазин - {category}\n\n"
    if status_message:
        caption += f"{status_message}\n"
    caption += f"💰 Ваш баланс: {balance} монет\nВыберите товар:"
    
    await callback.message.edit_caption(
        caption=caption,
        reply_markup=keyboard
    )

