"""
Инвентарь персонажа - управление предметами игрока
С системой артикулов для уникальной идентификации предметов
"""

import sqlite3
from typing import List, Tuple, Optional, Dict, Any
from .models import BaseDatabase


class PlayerInventoryDB(BaseDatabase):
    """
    Управление инвентарем игрока с системой артикулов
    """
    
    def __init__(self, db_path: str = "game.db"):
        super().__init__(db_path)
        self._ensure_inventory_tables()
    
    def _ensure_inventory_tables(self):
        """Создает таблицы инвентаря если не существуют"""
        query = '''
            CREATE TABLE IF NOT EXISTS player_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                item_sku TEXT NOT NULL,  -- АРТИКУЛ вместо названия
                item_name TEXT NOT NULL,  -- Название для удобства
                item_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                durability INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players (id),
                UNIQUE(player_id, item_sku)  -- Уникальность по артикулу
            )
        '''
        self.execute_query(query)
        print("🎯 Таблица player_inventory создана/проверена (с системой SKU)")
    
    def add_to_inventory(self, player_id: int, item_sku: str, item_name: str = None, item_type: str = None, durability: Optional[int] = None) -> bool:
        """
        Добавить предмет в инвентарь игрока по артикулу
        """
        try:
            # Если передано только название, получаем артикул
            if not item_sku and item_name:
                from .shop_catalog import ShopCatalogDB
                shop_db = ShopCatalogDB(self.db_path)
                item_sku = shop_db.get_sku_by_name(item_name)
                if not item_sku:
                    print(f"❌ Не найден артикул для товара: {item_name}")
                    return False
            
            # Если не переданы название и тип, получаем из каталога
            if not item_name or not item_type:
                from .shop_catalog import ShopCatalogDB
                shop_db = ShopCatalogDB(self.db_path)
                item_data = shop_db.get_item_by_sku(item_sku)
                if not item_data:
                    print(f"❌ Не найден товар с артикулом: {item_sku}")
                    return False
                
                if not item_name:
                    item_name = item_data[1]  # name из кортежа
                if not item_type:
                    item_type = item_data[2]  # category из кортежа
            
            # Если прочность не указана, получаем из каталога
            if durability is None:
                from .shop_catalog import ShopCatalogDB
                shop_db = ShopCatalogDB(self.db_path)
                item_data = shop_db.get_item_by_sku(item_sku)
                if item_data:
                    durability = item_data[5]  # durability из кортежа
                else:
                    durability = 1
            
            self.execute_query('''
                INSERT INTO player_inventory (player_id, item_sku, item_name, item_type, quantity, durability)
                VALUES (?, ?, ?, ?, 1, ?)
            ''', (player_id, item_sku, item_name, item_type, durability))
            
            print(f"✅ Добавлен предмет '{item_name}' (SKU: {item_sku}) в инвентарь игрока {player_id}")
            return True
            
        except sqlite3.IntegrityError:
            print(f"⚠️ Предмет с артикулом '{item_sku}' уже есть в инвентаре игрока {player_id}")
            return False
        except Exception as e:
            print(f"❌ Ошибка добавления в инвентарь: {e}")
            return False
    
    def add_to_inventory_by_name(self, player_id: int, item_name: str, item_type: str = None, durability: Optional[int] = None) -> bool:
        """
        Добавить предмет в инвентарь по названию (для обратной совместимости)
        """
        from .shop_catalog import ShopCatalogDB
        shop_db = ShopCatalogDB(self.db_path)
        sku = shop_db.get_sku_by_name(item_name)
        
        if not sku:
            print(f"❌ Не найден артикул для товара: {item_name}")
            return False
        
        return self.add_to_inventory(player_id, sku, item_name, item_type, durability)
    
    def get_player_inventory(self, player_id: int, item_type: Optional[str] = None) -> List[Tuple]:
        """
        Получить инвентарь игрока
        """
        if item_type:
            return self.fetch_all(
                "SELECT item_sku, item_name, item_type, quantity, durability FROM player_inventory WHERE player_id = ? AND item_type = ? ORDER BY item_type, item_name",
                (player_id, item_type)
            )
        else:
            return self.fetch_all(
                "SELECT item_sku, item_name, item_type, quantity, durability FROM player_inventory WHERE player_id = ? ORDER BY item_type, item_name",
                (player_id,)
            )
    
    def has_item(self, player_id: int, item_sku: str) -> bool:
        """Проверить, есть ли у игрока предмет по артикулу"""
        result = self.fetch_one(
            "SELECT 1 FROM player_inventory WHERE player_id = ? AND item_sku = ?",
            (player_id, item_sku)
        )
        return result is not None
    
    def has_item_by_name(self, player_id: int, item_name: str) -> bool:
        """Проверить, есть ли у игрока предмет по названию"""
        result = self.fetch_one(
            "SELECT 1 FROM player_inventory WHERE player_id = ? AND item_name = ?",
            (player_id, item_name)
        )
        return result is not None
    
    def get_item_durability(self, player_id: int, item_sku: str) -> Optional[int]:
        """Получить прочность предмета по артикулу"""
        result = self.fetch_one(
            "SELECT durability FROM player_inventory WHERE player_id = ? AND item_sku = ?",
            (player_id, item_sku)
        )
        return result[0] if result else None
    
    def update_durability(self, player_id: int, item_sku: str, new_durability: int) -> bool:
        """
        Обновить прочность предмета по артикулу
        """
        try:
            if new_durability <= 0:
                self.execute_query(
                    "DELETE FROM player_inventory WHERE player_id = ? AND item_sku = ?",
                    (player_id, item_sku)
                )
                print(f"🗑️ Предмет с артикулом '{item_sku}' удален из инвентаря (прочность 0)")
                return True
            else:
                self.execute_query(
                    "UPDATE player_inventory SET durability = ? WHERE player_id = ? AND item_sku = ?",
                    (new_durability, player_id, item_sku)
                )
                print(f"🔧 Прочность предмета '{item_sku}' обновлена: {new_durability}")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка обновления прочности: {e}")
            return False
    
    # Остальные методы аналогично обновляем для работы с артикулами...