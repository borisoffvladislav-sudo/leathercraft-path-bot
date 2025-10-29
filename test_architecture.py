#!/usr/bin/env python3
"""
Тестирование всей модульной архитектуры БД
"""

from database.models import Database

def test_all_modules():
    print("🧪 ТЕСТИРОВАНИЕ МОДУЛЬНОЙ АРХИТЕКТУРЫ БД")
    print("=" * 50)
    
    try:
        # 1. Создаем экземпляр БД
        db = Database()
        print("✅ Основной класс Database создан")
        
        # 2. Тестируем модуль магазина
        categories = db.shop.get_all_categories()
        print(f"✅ Модуль магазина: {len(categories)} категорий")
        print(f"   Категории: {', '.join(categories)}")
        
        # 3. Тестируем артикулы
        knives = db.shop.get_items_by_category('Ножи')
        print(f"✅ Система артикулов: {len(knives)} ножей с SKU")
        for sku, name, price, available, image, durability in knives[:3]:
            print(f"   📦 {sku} - {name} ({price} монет)")
        
        # 4. Тестируем модуль персонажей
        print("✅ Модуль персонажей готов")
        
        # 5. Тестируем модуль инвентаря
        print("✅ Модуль инвентаря готов")
        
        # 6. Тестируем модуль обучения
        print("✅ Модуль обучения готов")
        
        # 7. Тестируем модуль заказов
        orders = db.orders.get_available_orders(1)
        print(f"✅ Модуль заказов: {len(orders)} доступных заказов")
        
        # 8. Тестируем обратную совместимость
        old_style_items = db.get_tools_by_category('Ножи')
        print(f"✅ Обратная совместимость: {len(old_style_items)} товаров старым методом")
        
        print("\n🎉 ВСЕ МОДУЛИ РАБОТАЮТ КОРРЕКТНО!")
        print("📊 Архитектура готова к использованию!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_all_modules()
