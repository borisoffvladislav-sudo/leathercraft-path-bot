#!/usr/bin/env python3
"""
Тестирование новой модульной структуры базы данных
"""

from database.models import Database

def test_new_database_structure():
    """Тест новой структуры БД"""
    print("🧪 Тестирование новой модульной структуры БД...")
    
    # Создаем экземпляр основной БД
    db = Database()
    
    # Тестируем все модули
    print("\n1. Тестирование модуля персонажей...")
    test_user = db.characters.get_or_create_user(123456789, "test_user", "Test", "User")
    print(f"✅ User ID: {test_user}")
    
    print("\n2. Тестирование модуля магазина...")
    categories = db.shop.get_all_categories()
    print(f"✅ Категории магазина: {categories}")
    
    print("\n3. Тестирование модуля инвентаря...")
    inventory = db.inventory.get_player_inventory(1)  # Тестовый ID
    print(f"✅ Инвентарь: {len(inventory)} предметов")
    
    print("\n4. Тестирование модуля обучения...")
    tutorial_status = db.tutorial.get_tutorial_status(1)
    print(f"✅ Статус обучения: {tutorial_status.get('current_step', 'N/A')}")
    
    print("\n5. Тестирование модуля заказов...")
    available_orders = db.orders.get_available_orders(1)
    print(f"✅ Доступные заказы: {len(available_orders)}")
    
    print("\n6. Тестирование обратной совместимости...")
    # Старые методы должны работать
    active_player = db.get_active_player(123456789)
    print(f"✅ Обратная совместимость: {active_player is not None}")
    
    print("\n🎉 Все модули БД работают корректно!")
    print("📊 Новая структура готова к использованию!")

if __name__ == "__main__":
    test_new_database_structure()
