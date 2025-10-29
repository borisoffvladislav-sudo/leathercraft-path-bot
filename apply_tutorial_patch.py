#!/usr/bin/env python3
"""
АВТОМАТИЧЕСКИЙ ПАТЧ ДЛЯ TUTORIAL.PY
Применяет все необходимые правки для работы с системой артикулов
"""

import os
import re

def apply_patch():
    print("🎯 НАЧАЛО АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ TUTORIAL.PY")
    print("=" * 60)
    
    file_path = "routers/tutorial.py"
    backup_path = "routers/tutorial_backup.py"
    
    # Создаем резервную копию
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as original:
            with open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(original.read())
        print("✅ Создана резервная копия: routers/tutorial_backup.py")
    
    # Читаем исходный файл
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # === ПРАВКА 1: ЗАМЕНА ИМПОРТОВ И ДОБАВЛЕНИЕ КОНСТАНТ ===
    print("\n1. Обновляем импорты и добавляем константы артикулов...")
    
    # Заменяем импорт TutorialDatabase на Database
    content = content.replace(
        "from database.models import TutorialDatabase", 
        "from database.models import Database"
    )
    
    # Добавляем константы артикулов после импортов
    sku_constants = '''
# === СИСТЕМА АРТИКУЛОВ ДЛЯ ПРОВЕРКИ ТОВАРОВ ===

# Артикулы обязательных товаров для обучения
REQUIRED_TUTORIAL_SKUS = [
    "KNIFE_КАННОЖ",  # Канцелярский нож
    "PUNCH_ВЫСПРО",  # Высечные пробойники  
    "EDGE_МУЛЬТИТ",  # Мультитул 3 в 1
    "MAT_ДЕШРЕМ",    # Дешевая ременная заготовка
    "HW_ДЕШФУР",     # Дешевая фурнитура для ремней
    "THREAD_ШВЕМОС"  # Швейные МосНитки
]

# Маппинг артикулов на названия для сообщений
SKU_TO_NAME = {
    "KNIFE_КАННОЖ": "Канцелярский нож",
    "PUNCH_ВЫСПРО": "Высечные пробойники", 
    "EDGE_МУЛЬТИТ": "Мультитул 3 в 1",
    "MAT_ДЕШРЕМ": "Дешевая ременная заготовка",
    "HW_ДЕШФУР": "Дешевая фурнитура для ремней",
    "THREAD_ШВЕМОС": "Швейные МосНитки"
}
'''
    
    # Вставляем константы после импорта Database
    import_pattern = r"(from database\.models import Database\n)"
    content = re.sub(import_pattern, r"\1" + sku_constants + "\n", content)
    
    # === ПРАВКА 2: ОБНОВЛЕНИЕ ФУНКЦИИ buy_item() ===
    print("2. Обновляем функцию buy_item() для работы с артикулами...")
    
    # Находим и заменяем всю функцию buy_item
    old_buy_item_pattern = r'async def buy_item\(callback: CallbackQuery, state: FSMContext\):.*?await callback\.answer\("❌ Ошибка покупки", show_alert=True\)'
    
    new_buy_item = '''async def buy_item(callback: CallbackQuery, state: FSMContext):
    """Обработчик покупки товара с системой артикулов"""
    try:
        # Получаем артикул из callback data
        item_sku = callback.data.replace("buy_", "")
        print(f"🛒 Попытка покупки товара с артикулом: {item_sku}")
        
        # Восстанавливаем player_id если нужно
        data = await state.get_data()
        player_id = data.get('player_id')
        
        if not player_id:
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
        
        # Проверяем дубликаты по артикулу
        if db.tutorial.has_item_in_tutorial(player_id, item_sku):
            await callback.answer("✅ Я уже это купил", show_alert=True)
            return
        
        # Совершаем покупку
        new_balance = player_balance - item_price
        db.tutorial.update_player_balance(player_id, new_balance)
        db.tutorial.add_to_tutorial_inventory(player_id, item_sku, item_name)
        
        print(f"✅ Куплен товар: {item_name} (SKU: {item_sku}) за {item_price} монет")
        
        # Обновляем сообщение магазина
        await update_shop_category_message(callback, state, new_balance)
        
    except Exception as e:
        print(f"❌ Ошибка в buy_item: {e}")
        await callback.answer("❌ Ошибка покупки", show_alert=True)

async def update_shop_category_message(callback: CallbackQuery, state: FSMContext, new_balance: int):
    """Обновляет сообщение магазина после покупки"""
    try:
        data = await state.get_data()
        category = data.get('current_category', 'Ножи')
        
        db = Database()
        
        # Получаем товары категории
        items = db.shop.get_items_by_category(category)
        
        # Создаем клавиатуру
        builder = InlineKeyboardBuilder()
        
        player_id = data.get('player_id')
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
            f"🏪 Магазин - {category}\\n💰 Баланс: {new_balance} монет\\n\\n📋 Выберите товар:",
            reply_markup=builder.as_markup()
        )
        
    except Exception as e:
        print(f"❌ Ошибка обновления сообщения магазина: {e}")'''
    
    content = re.sub(old_buy_item_pattern, new_buy_item, content, flags=re.DOTALL)
    
    # === ПРАВКА 3: ОБНОВЛЕНИЕ ФУНКЦИИ shop_exit() ===
    print("3. Обновляем функцию shop_exit() для проверки по артикулам...")
    
    # Заменяем проверку инвентаря в shop_exit
    old_inventory_check = r'# Проверяем наличие всех обязательных товаров.*?has_all_required = all\(item in inventory_items for item in required_items\)'
    
    new_inventory_check = '''    # Проверяем наличие всех обязательных товаров по артикулам
    purchased_skus = [item[0] for item in inventory]
    missing_skus = [sku for sku in REQUIRED_TUTORIAL_SKUS if sku not in purchased_skus]
    has_all_required = len(missing_skus) == 0
    
    # Получаем читаемые названия недостающих товаров
    missing_items_text = ", ".join([SKU_TO_NAME.get(sku, sku) for sku in missing_skus]) if missing_skus else "все необходимое"'''
    
    content = re.sub(old_inventory_check, new_inventory_check, content, flags=re.DOTALL)
    
    # === ПРАВКА 4: ОБНОВЛЕНИЕ ФУНКЦИИ show_shop_category() ===
    print("4. Обновляем функцию show_shop_category()...")
    
    # Заменяем TutorialDatabase() на Database() в show_shop_category
    content = content.replace(
        "    tutorial_db = TutorialDatabase()",
        "    db = Database()"
    )
    
    # Заменяем вызовы методов
    content = content.replace("tutorial_db.get_shop_items_by_category", "db.shop.get_items_by_category")
    content = content.replace("tutorial_db.has_item_in_tutorial", "db.tutorial.has_item_in_tutorial")
    
    # Обновляем цикл для работы с артикулами
    old_loop_pattern = r'for item_name, price, available, image_path in items:'
    new_loop = '    for sku, name, price, available, image_path, durability in items:'
    content = content.replace(old_loop_pattern, new_loop)
    
    # Обновляем использование названия в цикле
    content = content.replace("item_name", "name")
    content = content.replace('f"buy_{item_name}"', 'f"buy_{sku}"')
    
    # === ПРАВКА 5: ОБНОВЛЕНИЕ ОСТАЛЬНЫХ ФУНКЦИЙ ===
    print("5. Обновляем остальные функции...")
    
    # Заменяем все оставшиеся TutorialDatabase() на Database()
    content = content.replace("TutorialDatabase()", "Database()")
    
    # Заменяем вызовы методов tutorial_db на db
    content = content.replace("tutorial_db.", "db.tutorial.")
    
    # === СОХРАНЕНИЕ РЕЗУЛЬТАТА ===
    print("6. Сохраняем обновленный файл...")
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print("✅ Файл routers/tutorial.py успешно обновлен!")
    print("\n📋 ВЫПОЛНЕННЫЕ ИЗМЕНЕНИЯ:")
    print("   ✅ Заменен TutorialDatabase на Database")
    print("   ✅ Добавлены константы артикулов")
    print("   ✅ Обновлена функция buy_item() для работы с SKU")
    print("   ✅ Обновлена функция shop_exit() для проверки по артикулам")
    print("   ✅ Обновлена функция show_shop_category() для работы с артикулами")
    print("   ✅ Все вызовы методов обновлены для новой архитектуры")
    
    print(f"\n💡 Создана резервная копия: {backup_path}")
    print("🚀 Запустите бота для тестирования: python bot.py")

if __name__ == "__main__":
    apply_patch()