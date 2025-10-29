"""
ПАТЧ ДЛЯ TUTORIAL.PY - Обновление для работы с артикулами
Добавить этот код в существующий файл routers/tutorial.py
"""

# === КОНСТАНТЫ ДЛЯ ПРОВЕРКИ АРТИКУЛОВ ===

# Артикулы обязательных товаров для обучения
REQUIRED_TUTORIAL_SKUS = [
    "KNIFE_KAN",      # Канцелярский нож
    "PUNCH_VYS",      # Высечные пробойники  
    "EDGE_MUL",       # Мультитул 3 в 1
    "MAT_DES",        # Дешевая ременная заготовка
    "HW_DES",         # Дешевая фурнитура для ремней
    "THREAD_SHV"      # Швейные МосНитки (новая)
]

# Маппинг артикулов на названия для сообщений
SKU_TO_NAME = {
    "KNIFE_KAN": "Канцелярский нож",
    "PUNCH_VYS": "Высечные пробойники",
    "EDGE_MUL": "Мультитул 3 в 1", 
    "MAT_DES": "Дешевая ременная заготовка",
    "HW_DES": "Дешевая фурнитура для ремней",
    "THREAD_SHV": "Швейные МосНитки"
}

# === ОБНОВЛЕННЫЕ ФУНКЦИИ ===

async def check_tutorial_inventory_complete(player_id: int) -> tuple[bool, list]:
    """
    Проверяет, куплены ли все обязательные товары по артикулам
    Возвращает (bool, list) - (полный комплект, список недостающих SKU)
    """
    try:
        from database.models import Database
        db = Database()
        
        # Получаем учебный инвентарь
        tutorial_inventory = db.tutorial.get_tutorial_inventory(player_id)
        purchased_skus = [item[0] for item in tutorial_inventory]  # item_sku теперь первый элемент
        
        missing_skus = []
        for required_sku in REQUIRED_TUTORIAL_SKUS:
            if required_sku not in purchased_skus:
                missing_skus.append(required_sku)
        
        is_complete = len(missing_skus) == 0
        return is_complete, missing_skus
        
    except Exception as e:
        print(f"❌ Ошибка проверки инвентаря: {e}")
        return False, REQUIRED_TUTORIAL_SKUS.copy()


async def get_missing_items_names(missing_skus: list) -> str:
    """Преобразует список артикулов в читаемые названия"""
    missing_names = []
    for sku in missing_skus:
        if sku in SKU_TO_NAME:
            missing_names.append(SKU_TO_NAME[sku])
        else:
            missing_names.append(sku)  # fallback
    
    return ", ".join(missing_names) if missing_names else "все необходимое"


# === ОБНОВЛЕНИЕ В ФУНКЦИИ buy_item() ===

# ЗАМЕНИТЕ существующую функцию buy_item() на эту:

async def buy_item(callback: CallbackQuery, state: FSMContext):
    """Обработчик покупки товара с системой артикулов"""
    try:
        # Получаем артикул из callback data
        item_sku = callback.data.replace("buy_", "")
        print(f"🛒 Попытка покупки товара с артикулом: {item_sku}")
        
        # Восстанавливаем player_id если нужно
        data = await state.get_data()
        player_id = data.get('player_id')
        
        if not player_id:
            from database.models import Database
            db = Database()
            user = callback.from_user
            player_data = db.characters.get_active_player(user.id)
            if player_data:
                player_id = player_data[0]
                await state.update_data(player_id=player_id)
                print(f"🎯 Восстановлен player_id: {player_id}")
            else:
                await callback.answer("❌ Ошибка: персонаж не найден", show_alert=True)
                return
        
        from database.models import Database
        db = Database()
        
        # Получаем информацию о товаре по артикулу
        item_data = db.shop.get_item_by_sku(item_sku)
        if not item_data:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return
        
        item_name = item_data[1]  # Название товара
        item_price = item_data[2]  # Цена
        available_in_tutorial = item_data[3]  # Доступность в обучении
        
        # Проверяем доступность в обучении
        if not available_in_tutorial:
            await callback.answer("🔒 Этот товар недоступен в обучении", show_alert=True)
            return
        
        # Проверяем баланс
        player_balance = db.tutorial.get_player_balance(player_id)
        if player_balance < item_price:
            await callback.answer("❌ Недостаточно монет!", show_alert=True)
            return
        
        # Проверяем дубликаты
        if db.tutorial.has_item_in_tutorial(player_id, item_sku):
            await callback.answer("✅ Я уже это купил", show_alert=True)
            return
        
        # Совершаем покупку
        new_balance = player_balance - item_price
        db.tutorial.update_player_balance(player_id, new_balance)
        db.tutorial.add_to_tutorial_inventory(player_id, item_sku, item_name)
        
        print(f"✅ Куплен товар: {item_name} (SKU: {item_sku}) за {item_price} монет")
        
        # Обновляем сообщение магазина
        await update_shop_category_message(callback, item_sku, new_balance)
        
    except Exception as e:
        print(f"❌ Ошибка в buy_item: {e}")
        await callback.answer("❌ Ошибка покупки", show_alert=True)


async def update_shop_category_message(callback: CallbackQuery, purchased_sku: str, new_balance: int):
    """Обновляет сообщение магазина после покупки"""
    try:
        data = await callback.message.edit_reply_markup()
        category = data.get('category', 'Ножи')  # Получаем категорию из состояния
        
        from database.models import Database
        db = Database()
        
        # Получаем товары категории
        items = db.shop.get_items_by_category(category)
        
        # Создаем клавиатуру
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        player_id = (await callback.get_state().get_data()).get('player_id')
        tutorial_inventory = db.tutorial.get_tutorial_inventory(player_id)
        purchased_skus = [item[0] for item in tutorial_inventory]
        
        for sku, name, price, available, image_path, durability in items:
            if sku in purchased_skus:
                builder.button(text=f"✅ {name} - {price} монет", callback_data=f"already_bought_{sku}")
            elif not available:
                builder.button(text=f"🔒 {name} - {price} монет", callback_data=f"locked_{sku}")
            elif new_balance < price:
                builder.button(text=f"❌ {name} - {price} монет", callback_data=f"no_money_{sku}")
            else:
                builder.button(text=f"🛒 {name} - {price} монет", callback_data=f"buy_{sku}")
        
        builder.button(text="🔙 Назад", callback_data="back_to_shop_menu")
        builder.adjust(1)
        
        # Обновляем сообщение
        await callback.message.edit_text(
            f"🏪 Магазин - {category}\n💰 Баланс: {new_balance} монет\n\n📋 Выберите товар:",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        print(f"❌ Ошибка обновления сообщения магазина: {e}")