#!/usr/bin/env python3
"""
ИНТЕРАКТИВНЫЙ ТЕСТЕР - пошаговое тестирование сценариев
"""

import sqlite3
from database.models import Database, TutorialDatabase

def test_database_connection():
    """Тестирует подключение к БД"""
    print("🔍 Тестируем подключение к БД...")
    try:
        db = Database()
        print("✅ Подключение к game.db успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_tables_exist():
    """Проверяет существование таблиц"""
    print("🔍 Проверяем наличие таблиц...")
    required_tables = ['players', 'tutorial_progress', 'tutorial_inventory', 'shop_items']
    
    try:
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        for table in required_tables:
            if table in existing_tables:
                print(f"✅ Таблица {table} существует")
            else:
                print(f"❌ Таблица {table} отсутствует")
                
        conn.close()
        return all(table in existing_tables for table in required_tables)
        
    except Exception as e:
        print(f"❌ Ошибка проверки таблиц: {e}")
        return False

def test_shop_items():
    """Проверяет товары магазина"""
    print("🔍 Проверяем товары магазина...")
    try:
        tutorial_db = TutorialDatabase()
        categories = ["Ножи", "Пробойники", "Торцбилы", "Материалы", "Фурнитура", "Химия"]
        
        for category in categories:
            items = tutorial_db.get_shop_items_by_category(category)
            if items:
                print(f"✅ Категория {category}: {len(items)} товаров")
            else:
                print(f"❌ Категория {category}: нет товаров")
                
        return True
    except Exception as e:
        print(f"❌ Ошибка проверки магазина: {e}")
        return False

def run_interactive_test():
    """Запускает интерактивное тестирование"""
    print("🎮 ИНТЕРАКТИВНОЕ ТЕСТИРОВАНИЕ")
    print("=" * 50)
    
    # Запускаем тесты
    tests = [
        ("Подключение к БД", test_database_connection),
        ("Проверка таблиц", test_tables_exist),
        ("Товары магазина", test_shop_items),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    # Выводим итоги
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"   {status}: {test_name}")

if __name__ == "__main__":
    run_interactive_test()