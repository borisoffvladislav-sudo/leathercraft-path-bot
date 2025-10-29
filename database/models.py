"""
Базовые модели и подключение к базе данных
Основной класс Database обеспечивает обратную совместимость
"""

import sqlite3
import os
from typing import Optional, List, Tuple

class BaseDatabase:
    """
    Базовый класс для всех модулей базы данных
    Обеспечивает общие методы подключения и управления таблицами
    """
    
    def __init__(self, db_path: str = "game.db"):
        self.db_path = db_path
        self._ensure_database_dir()
    
    def _ensure_database_dir(self):
        """Создает папку для базы данных если не существует"""
         # Если путь содержит папки - создаем их
        if os.path.dirname(self.db_path) and not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Создает новое соединение для каждого запроса
        Для избежания блокировок БД
        """
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Выполняет SQL запрос с параметрами
        Возвращает курсор с результатами
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[tuple]:
        """Выполняет запрос и возвращает одну строку"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(query, params)
            return cursor.fetchone()
        finally:
            conn.close()
    
    def fetch_all(self, query: str, params: tuple = ()) -> List[tuple]:
        """Выполняет запрос и возвращает все строки"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
        finally:
            conn.close()


class Database:
    """
    Основной класс для работы со всеми модулями БД
    Обеспечивает обратную совместимость со старым кодом
    """
    
    def __init__(self, db_path: str = "game.db"):
        self.db_path = db_path
        
        # Инициализация всех модулей БД
        from .shop_catalog import ShopCatalogDB
        from .player_inventory import PlayerInventoryDB
        from .characters import CharactersDB
        from .tutorial_progress import TutorialProgressDB
        from .orders import OrdersDB
        
        self.shop = ShopCatalogDB(db_path)
        self.inventory = PlayerInventoryDB(db_path)
        self.characters = CharactersDB(db_path)
        self.tutorial = TutorialProgressDB(db_path)
        self.orders = OrdersDB(db_path)
    
    # === МЕТОДЫ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ ===
    
    # Магазин
    def get_tools_by_category(self, category: str) -> List[tuple]:
        """Совместимость со старым кодом"""
        return self.shop.get_items_by_category(category)
    
    def get_shop_items_by_category(self, category: str) -> List[tuple]:
        """Совместимость с TutorialDatabase"""
        return self.shop.get_items_by_category(category)
    
    # Инвентарь
    def add_to_inventory(self, player_id: int, item_name: str, item_type: str) -> bool:
        """Совместимость со старым кодом"""
        return self.inventory.add_to_inventory(player_id, item_name, item_type)
    
    def get_player_inventory(self, player_id: int, item_type: str = None) -> List[tuple]:
        """Совместимость со старым кодом"""
        return self.inventory.get_player_inventory(player_id, item_type)
    
    # Персонажи
    def get_active_player(self, telegram_id: int) -> Optional[tuple]:
        """Совместимость со старым кодом"""
        return self.characters.get_active_player(telegram_id)
    
    def add_player(self, user_id: int, name: str, player_class: str) -> int:
        """Совместимость со старым кодом"""
        return self.characters.add_player(user_id, name, player_class)
    
    # Обучение
    def init_tutorial_progress(self, player_id: int) -> bool:
        """Совместимость с TutorialDatabase"""
        return self.tutorial.init_tutorial_progress(player_id)
    
    def update_player_balance(self, player_id: int, new_balance: int) -> bool:
        """Совместимость с TutorialDatabase"""
        return self.tutorial.update_player_balance(player_id, new_balance)
    
    def add_to_tutorial_inventory(self, player_id: int, item_name: str, item_type: str) -> bool:
        """Совместимость с TutorialDatabase"""
        return self.tutorial.add_to_tutorial_inventory(player_id, item_name, item_type)


def check_tables():
    """Проверка создания всех таблиц (для отладки)"""
    db = Database()
    print("✅ Все модули БД инициализированы")
    print(f"📊 Путь к БД: {db.db_path}")
    
    # Проверяем доступность методов
    test_methods = [
        db.shop.get_items_by_category,
        db.inventory.get_player_inventory, 
        db.characters.get_active_player,
        db.tutorial.init_tutorial_progress
    ]
    
    for method in test_methods:
        print(f"✅ {method.__name__} доступен")
    
    print("🎯 Проверка БД завершена успешно!")