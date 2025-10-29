"""
Прогресс обучения - управление этапами обучения, учебным инвентарем
"""

import sqlite3
from typing import List, Tuple, Optional, Dict, Any
from .models import BaseDatabase


class TutorialProgressDB(BaseDatabase):
    """
    Управление прогрессом обучения
    Этапы, учебный инвентарь, баланс в обучении
    """
    
    def __init__(self, db_path: str = "game.db"):
        super().__init__(db_path)
        self._ensure_tutorial_tables()
    
    def _ensure_tutorial_tables(self):
        """Создает таблицы для обучения если не существуют"""
        # Прогресс обучения
        progress_query = '''
            CREATE TABLE IF NOT EXISTS tutorial_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER UNIQUE NOT NULL,
                current_step INTEGER DEFAULT 1,
                player_balance INTEGER DEFAULT 1500,
                completed_steps TEXT DEFAULT '',
                is_completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players (id)
            )
        '''
        self.execute_query(progress_query)
        
        # Учебный инвентарь
        inventory_query = '''
            CREATE TABLE IF NOT EXISTS tutorial_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                item_type TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players (id),
                UNIQUE(player_id, item_name)
            )
        '''
        self.execute_query(inventory_query)
        print("🎯 Таблицы tutorial_progress и tutorial_inventory созданы/проверены")
    
    def init_tutorial_progress(self, player_id: int) -> bool:
        """
        Инициализировать прогресс обучения для нового персонажа
        Возвращает True если успешно
        """
        try:
            # Проверяем, есть ли уже запись
            existing = self.fetch_one(
                "SELECT 1 FROM tutorial_progress WHERE player_id = ?",
                (player_id,)
            )
            
            if existing:
                print(f"✅ Прогресс обучения для персонажа {player_id} уже инициализирован")
                return True
            
            # Создаем новую запись
            self.execute_query(
                "INSERT INTO tutorial_progress (player_id, current_step, player_balance) VALUES (?, 1, 1500)",
                (player_id,)
            )
            print(f"✅ Инициализирован прогресс обучения для персонажа {player_id}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка инициализации обучения: {e}")
            return False
    
    def get_tutorial_progress(self, player_id: int) -> Optional[Tuple]:
        """Получить прогресс обучения персонажа"""
        return self.fetch_one(
            "SELECT current_step, player_balance, completed_steps, is_completed FROM tutorial_progress WHERE player_id = ?",
            (player_id,)
        )
    
    def update_tutorial_progress(self, player_id: int, current_step: int = None, completed_steps: str = None) -> bool:
        """Обновить прогресс обучения"""
        try:
            update_fields = []
            params = []
            
            if current_step is not None:
                update_fields.append("current_step = ?")
                params.append(current_step)
            
            if completed_steps is not None:
                update_fields.append("completed_steps = ?")
                params.append(completed_steps)
            
            # Всегда обновляем updated_at
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            params.append(player_id)
            
            query = f"UPDATE tutorial_progress SET {', '.join(update_fields)} WHERE player_id = ?"
            self.execute_query(query, tuple(params))
            
            print(f"✅ Прогресс обучения персонажа {player_id} обновлен: шаг {current_step}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления прогресса: {e}")
            return False
    
    def complete_tutorial(self, player_id: int) -> bool:
        """Отметить обучение как завершенное"""
        try:
            self.execute_query(
                "UPDATE tutorial_progress SET is_completed = TRUE, current_step = 999, updated_at = CURRENT_TIMESTAMP WHERE player_id = ?",
                (player_id,)
            )
            print(f"🎓 Обучение завершено для персонажа {player_id}")
            return True
        except Exception as e:
            print(f"❌ Ошибка завершения обучения: {e}")
            return False
    
    def update_player_balance(self, player_id: int, new_balance: int) -> bool:
        """Обновить учебный баланс игрока"""
        try:
            self.execute_query(
                "UPDATE tutorial_progress SET player_balance = ? WHERE player_id = ?",
                (new_balance, player_id)
            )
            print(f"💰 Учебный баланс персонажа {player_id} обновлен: {new_balance}")
            return True
        except Exception as e:
            print(f"❌ Ошибка обновления баланса: {e}")
            return False
    
    def get_player_balance(self, player_id: int) -> int:
        """Получить учебный баланс игрока"""
        result = self.fetch_one(
            "SELECT player_balance FROM tutorial_progress WHERE player_id = ?",
            (player_id,)
        )
        return result[0] if result else 1500  # Значение по умолчанию
    
    def add_to_tutorial_inventory(self, player_id: int, item_name: str, item_type: str) -> bool:
        """Добавить предмет в учебный инвентарь"""
        try:
            # Проверяем, есть ли уже предмет
            existing = self.fetch_one(
                "SELECT quantity FROM tutorial_inventory WHERE player_id = ? AND item_name = ?",
                (player_id, item_name)
            )
            
            if existing:
                # Увеличиваем количество
                new_quantity = existing[0] + 1
                self.execute_query(
                    "UPDATE tutorial_inventory SET quantity = ? WHERE player_id = ? AND item_name = ?",
                    (new_quantity, player_id, item_name)
                )
            else:
                # Добавляем новый предмет
                self.execute_query(
                    "INSERT INTO tutorial_inventory (player_id, item_name, item_type, quantity) VALUES (?, ?, ?, 1)",
                    (player_id, item_name, item_type)
                )
            
            print(f"✅ Предмет '{item_name}' добавлен в учебный инвентарь игрока {player_id}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка добавления в учебный инвентарь: {e}")
            return False
    
    def get_tutorial_inventory(self, player_id: int, item_type: str = None) -> List[Tuple]:
        """Получить учебный инвентарь игрока"""
        if item_type:
            return self.fetch_all(
                "SELECT item_name, item_type, quantity FROM tutorial_inventory WHERE player_id = ? AND item_type = ? ORDER BY item_type, item_name",
                (player_id, item_type)
            )
        else:
            return self.fetch_all(
                "SELECT item_name, item_type, quantity FROM tutorial_inventory WHERE player_id = ? ORDER BY item_type, item_name",
                (player_id,)
            )
    
    def has_item_in_tutorial(self, player_id: int, item_name: str) -> bool:
        """Проверить, есть ли предмет в учебном инвентаре"""
        result = self.fetch_one(
            "SELECT 1 FROM tutorial_inventory WHERE player_id = ? AND item_name = ?",
            (player_id, item_name)
        )
        return result is not None
    
    def get_tutorial_inventory_summary(self, player_id: int) -> Dict[str, Any]:
        """Получить сводку по учебному инвентарю"""
        inventory = self.get_tutorial_inventory(player_id)
        
        summary = {
            "total_items": len(inventory),
            "categories": {},
            "items": []
        }
        
        for item_name, item_type, quantity in inventory:
            if item_type not in summary["categories"]:
                summary["categories"][item_type] = 0
            summary["categories"][item_type] += quantity
            
            summary["items"].append({
                "name": item_name,
                "type": item_type,
                "quantity": quantity
            })
        
        return summary
    
    def clear_tutorial_inventory(self, player_id: int) -> bool:
        """Очистить учебный инвентарь (для тестирования)"""
        try:
            self.execute_query(
                "DELETE FROM tutorial_inventory WHERE player_id = ?",
                (player_id,)
            )
            print(f"🗑️ Учебный инвентарь игрока {player_id} очищен")
            return True
        except Exception as e:
            print(f"❌ Ошибка очистки инвентаря: {e}")
            return False
    
    def get_tutorial_status(self, player_id: int) -> Dict[str, Any]:
        """Получить полный статус обучения"""
        progress = self.get_tutorial_progress(player_id)
        inventory_summary = self.get_tutorial_inventory_summary(player_id)
        
        if not progress:
            return {"error": "Прогресс обучения не найден"}
        
        return {
            "current_step": progress[0],
            "player_balance": progress[1],
            "completed_steps": progress[2],
            "is_completed": progress[3],
            "inventory": inventory_summary
        }