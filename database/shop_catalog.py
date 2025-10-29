"""
Каталог магазина - управление товарами, категориями, ценами
С системой артикулов (SKU) для уникальной идентификации
"""

import sqlite3
from typing import List, Tuple, Optional, Dict, Any
from .models import BaseDatabase


class ShopCatalogDB(BaseDatabase):
    """
    Управление каталогом магазина с системой артикулов
    """
    
    def __init__(self, db_path: str = "game.db"):
        super().__init__(db_path)
        self._ensure_shop_tables()
        self.init_shop_items()
    
    def _ensure_shop_tables(self):
        """Создает таблицы для магазина если не существуют"""
        query = '''
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,  -- УНИКАЛЬНЫЙ АРТИКУЛ
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL,
                available_in_tutorial BOOLEAN DEFAULT FALSE,
                image_path TEXT,
                durability INTEGER DEFAULT 10,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        self.execute_query(query)
        print("🎯 Таблица shop_items создана/проверена (с системой SKU)")
    
    def _generate_sku(self, category: str, name: str) -> str:
        """
        Генерирует уникальный артикул на основе категории и названия
        Формат: КАТ_СОКРАЩЕНИЕ_ЦИФРЫ
        """
        # Сокращения для категорий
        category_map = {
            "Ножи": "KNIFE",
            "Пробойники": "PUNCH", 
            "Торцбилы": "EDGE",
            "Материалы": "MAT",
            "Фурнитура": "HW",
            "Химия": "CHEM",
            "Нитки": "THREAD"
        }
        
        # Базовое сокращение названия (первые 3-4 буквы)
        name_short = ''.join([word[:3].upper() for word in name.split()[:2]])
        
        # Генерируем SKU
        base_sku = f"{category_map.get(category, 'ITEM')}_{name_short}"
        
        # Проверяем уникальность и добавляем цифру если нужно
        counter = 1
        sku = base_sku
        while self._sku_exists(sku):
            sku = f"{base_sku}_{counter}"
            counter += 1
            
        return sku
    
    def _sku_exists(self, sku: str) -> bool:
        """Проверяет существует ли артикул"""
        result = self.fetch_one("SELECT 1 FROM shop_items WHERE sku = ?", (sku,))
        return result is not None
    
    def init_shop_items(self):
        """Инициализация товаров магазина с артикулами"""
        # Проверяем, есть ли уже товары
        existing_items = self.fetch_all("SELECT COUNT(*) FROM shop_items")
        if existing_items[0][0] > 0:
            print("✅ Товары магазина уже инициализированы")
            return
        
        items = [
            # Ножи
            ("Канцелярский нож", "Ножи", 300, True, "images/shop/knife_cheap.jpg", 5, "Простой нож для начинающих"),
            ("Нож SDI", "Ножи", 900, False, "images/shop/knife_mid.jpg", 15, "Качественный нож для профи"),
            ("Шорный нож", "Ножи", 3600, False, "images/shop/knife_pro.jpg", 30, "Профессиональный шорный нож"),
            
            # Пробойники
            ("Высечные пробойники", "Пробойники", 280, True, "images/shop/punch_set.jpg", 8, "Набор пробойников для начала"),
            ("Пробойники Wuta", "Пробойники", 840, False, "images/shop/punch_wuta.jpg", 20, "Качественные пробойники Wuta"),
            ("Пробойники Sinabroks", "Пробойники", 3360, False, "images/shop/punch_storybrook.jpg", 50, "Профессиональные пробойники"),
            
            # Торцбилы
            ("Мультитул 3 в 1", "Торцбилы", 250, True, "images/shop/edge_slicker.jpg", 10, "Мультитул для обработки кромки"),
            ("Торцбил Wuta", "Торцбилы", 750, False, "images/shop/edge_wuta.jpg", 25, "Качественный торцбил"),
            ("Профессиональный торцбил", "Торцбилы", 3000, False, "images/shop/edge_pro.jpg", 50, "Профессиональный инструмент"),
            
            # Материалы
            ("Дешевая ременная заготовка", "Материалы", 150, True, "images/shop/leather_cheap.jpg", 1, "Недорогая кожа для тренировки"),
            ("Обычная ременная заготовка", "Материалы", 450, False, "images/shop/leather_mid.jpg", 1, "Качественная кожа"),
            ("Дорогая ременная заготовка", "Материалы", 1800, False, "images/shop/leather_expensive.jpg", 1, "Премиальная кожа"),
            
            # Фурнитура
            ("Дешевая фурнитура для ремней", "Фурнитура", 100, True, "images/shop/hardware_belts.jpg", 1, "Простая фурнитура"),
            ("Нержавейка для ремней", "Фурнитура", 300, False, "images/shop/hardware_wallets.jpg", 1, "Качественная нержавейка"),
            ("Латунная фурнитура", "Фурнитура", 1200, False, "images/shop/hardware_bags.jpg", 1, "Премиальная латунь"),
            
            # Химия
            ("Пчелиный воск", "Химия", 80, True, "images/shop/wax.jpg", 1, "Натуральный пчелиный воск"),
            ("Масловосковые смеси", "Химия", 240, False, "images/shop/wax_mix.jpg", 1, "Специальные смеси"),
            ("Профессиональная косметика", "Химия", 960, False, "images/shop/pro_cosmetics.jpg", 1, "Профессиональные средства"),
            
            # Нитки
            ("Швейные МосНитки", "Нитки", 150, True, "images/shop/threads_cheap.jpg", 1, "Прочные хлопковые нитки"),
            ("Синтетические нитки", "Нитки", 450, False, "images/shop/threads_mid.jpg", 1, "Синтетические нитки"),
            ("Льняные нитки", "Нитки", 1800, False, "images/shop/threads_pro.jpg", 1, "Натуральные льняные нитки"),
        ]
        
        try:
            for item in items:
                name, category, price, available, image_path, durability, description = item
                sku = self._generate_sku(category, name)
                
                self.execute_query('''
                    INSERT INTO shop_items (sku, name, category, price, available_in_tutorial, image_path, durability, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (sku, name, category, price, available, image_path, durability, description))
                
                print(f"✅ Добавлен товар: {name} (SKU: {sku})")
            
            print(f"🎯 Всего добавлено {len(items)} товаров с артикулами")
        except sqlite3.IntegrityError:
            print("✅ Товары уже существуют в БД")
    
    def get_items_by_category(self, category: str) -> List[Tuple]:
        """Получить все товары категории"""
        return self.fetch_all(
            "SELECT sku, name, price, available_in_tutorial, image_path, durability FROM shop_items WHERE category = ? ORDER BY price",
            (category,)
        )
    
    def get_item_by_sku(self, sku: str) -> Optional[Tuple]:
        """Получить товар по артикулу"""
        return self.fetch_one(
            "SELECT sku, name, price, available_in_tutorial, image_path, durability, description FROM shop_items WHERE sku = ?",
            (sku,)
        )
    
    def get_item_by_name(self, item_name: str) -> Optional[Tuple]:
        """Получить товар по названию (для обратной совместимости)"""
        return self.fetch_one(
            "SELECT sku, name, price, available_in_tutorial, image_path, durability, description FROM shop_items WHERE name = ?",
            (item_name,)
        )
    
    def get_sku_by_name(self, item_name: str) -> Optional[str]:
        """Получить артикул по названию товара"""
        result = self.fetch_one("SELECT sku FROM shop_items WHERE name = ?", (item_name,))
        return result[0] if result else None
    
    def get_name_by_sku(self, sku: str) -> Optional[str]:
        """Получить название товара по артикулу"""
        result = self.fetch_one("SELECT name FROM shop_items WHERE sku = ?", (sku,))
        return result[0] if result else None
    
    # Остальные методы остаются без изменений...
    def get_all_categories(self) -> List[str]:
        """Получить все категории товаров"""
        result = self.fetch_all("SELECT DISTINCT category FROM shop_items ORDER BY category")
        return [row[0] for row in result]
    
    def get_tutorial_items(self) -> List[Tuple]:
        """Получить товары доступные в обучении"""
        return self.fetch_all(
            "SELECT sku, name, category, price, image_path FROM shop_items WHERE available_in_tutorial = TRUE ORDER BY category, price"
        )
    
    def get_tutorial_items_skus(self) -> List[str]:
        """Получить артикулы товаров доступных в обучении"""
        result = self.fetch_all(
            "SELECT sku FROM shop_items WHERE available_in_tutorial = TRUE"
        )
        return [row[0] for row in result]