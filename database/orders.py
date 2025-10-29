"""
Система заказов - управление заказами, выполнением, наградами
(Будущий функционал для системы крафта)
"""

import sqlite3
import json
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from .models import BaseDatabase


class OrdersDB(BaseDatabase):
    """
    Управление системой заказов
    Заказы, выполнение, награды, прогресс клиентов
    """
    
    def __init__(self, db_path: str = "game.db"):
        super().__init__(db_path)
        self._ensure_orders_tables()
        self.init_default_orders()
    
    def _ensure_orders_tables(self):
        """Создает таблицы для системы заказов если не существуют"""
        # Таблица шаблонов заказов
        orders_query = '''
            CREATE TABLE IF NOT EXISTS order_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                required_level INTEGER DEFAULT 1,
                difficulty INTEGER DEFAULT 1,
                base_reward INTEGER DEFAULT 100,
                required_items TEXT,  -- JSON с требуемыми предметами
                required_tools TEXT,  -- JSON с требуемыми инструментами
                time_limit INTEGER DEFAULT 24,  -- В часах
                category TEXT DEFAULT 'ремни',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        self.execute_query(orders_query)
        
        # Таблица активных заказов игроков
        player_orders_query = '''
            CREATE TABLE IF NOT EXISTS player_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                template_id INTEGER NOT NULL,
                status TEXT DEFAULT 'active',  -- active, completed, failed, cancelled
                quality INTEGER DEFAULT 0,     -- Качество выполнения (0-100)
                reward INTEGER DEFAULT 0,      -- Фактическая награда
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                deadline TIMESTAMP NULL,
                used_items TEXT,               -- JSON с использованными предметами
                used_tools TEXT,               -- JSON с использованными инструментами
                client_satisfaction INTEGER DEFAULT 0,
                FOREIGN KEY (player_id) REFERENCES players (id),
                FOREIGN KEY (template_id) REFERENCES order_templates (id)
            )
        '''
        self.execute_query(player_orders_query)
        
        # Таблица клиентов и их предпочтений
        clients_query = '''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                preferences TEXT,  -- JSON с предпочтениями клиента
                base_reputation INTEGER DEFAULT 0,
                favorite_category TEXT DEFAULT 'ремни',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        self.execute_query(clients_query)
        
        print("🎯 Таблицы системы заказов созданы/проверены")
    
    def init_default_orders(self):
        """Инициализация стандартных заказов"""
        # Проверяем, есть ли уже заказы
        existing_orders = self.fetch_all("SELECT COUNT(*) FROM order_templates")
        if existing_orders[0][0] > 0:
            print("✅ Стандартные заказы уже инициализированы")
            return
        
        default_orders = [
            {
                "name": "Простой ремень",
                "description": "Клиенту нужен простой кожаный ремень на пряжке",
                "required_level": 1,
                "difficulty": 1,
                "base_reward": 200,
                "required_items": '{"Дешевая ременная заготовка": 1, "Дешевая фурнитура для ремней": 1}',
                "required_tools": '{"Канцелярский нож": 1, "Мультитул 3 в 1": 1}',
                "time_limit": 24,
                "category": "ремни"
            },
            {
                "name": "Ремень с тиснением", 
                "description": "Ремень с простым тиснением для особого случая",
                "required_level": 2,
                "difficulty": 2,
                "base_reward": 400,
                "required_items": '{"Обычная ременная заготовка": 1, "Нержавейка для ремней": 1, "Пчелиный воск": 1}',
                "required_tools": '{"Канцелярский нож": 1, "Мультитул 3 в 1": 1, "Высечные пробойники": 1}',
                "time_limit": 48,
                "category": "ремни"
            },
            {
                "name": "Простой картхолдер",
                "description": "Минималистичный держатель для банковских карт",
                "required_level": 1, 
                "difficulty": 1,
                "base_reward": 150,
                "required_items": '{"Дешевая ременная заготовка": 1, "Швейные МосНитки": 1}',
                "required_tools": '{"Канцелярский нож": 1, "Срочный пробойник PFG": 1}',
                "time_limit": 24,
                "category": "аксессуары"
            },
            {
                "name": "Кошелек с отделениями",
                "description": "Кошелек с несколькими отделениями для карт и денег",
                "required_level": 3,
                "difficulty": 3,
                "base_reward": 600,
                "required_items": '{"Дорогая ременная заготовка": 1, "Льняные нитки": 1, "Пчелиный воск": 1}',
                "required_tools": '{"Нож SDI": 1, "Пробойники Wuta": 1, "Торцбил Wuta": 1}',
                "time_limit": 72,
                "category": "аксессуары"
            }
        ]
        
        try:
            for order in default_orders:
                self.execute_query('''
                    INSERT INTO order_templates (name, description, required_level, difficulty, base_reward, 
                                               required_items, required_tools, time_limit, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    order["name"], order["description"], order["required_level"], 
                    order["difficulty"], order["base_reward"], order["required_items"],
                    order["required_tools"], order["time_limit"], order["category"]
                ))
            
            print(f"✅ Добавлено {len(default_orders)} стандартных заказов")
        except Exception as e:
            print(f"❌ Ошибка инициализации заказов: {e}")
    
    def get_available_orders(self, player_level: int) -> List[Tuple]:
        """Получить доступные заказы для игрока по уровню"""
        return self.fetch_all('''
            SELECT id, name, description, required_level, difficulty, base_reward, 
                   required_items, required_tools, time_limit, category
            FROM order_templates 
            WHERE required_level <= ? AND is_active = TRUE
            ORDER BY required_level, difficulty
        ''', (player_level,))
    
    def create_player_order(self, player_id: int, template_id: int) -> int:
        """Создать активный заказ для игрока"""
        try:
            # Получаем шаблон заказа
            template = self.fetch_one(
                "SELECT time_limit, base_reward FROM order_templates WHERE id = ?",
                (template_id,)
            )
            
            if not template:
                return 0
            
            time_limit_hours = template[0]
            deadline = datetime.now().timestamp() + (time_limit_hours * 3600)
            
            cursor = self.execute_query('''
                INSERT INTO player_orders (player_id, template_id, deadline, reward)
                VALUES (?, ?, datetime(?, 'unixepoch'), ?)
            ''', (player_id, template_id, deadline, template[1]))
            
            order_id = cursor.lastrowid
            print(f"✅ Создан заказ {order_id} для игрока {player_id}")
            return order_id
            
        except Exception as e:
            print(f"❌ Ошибка создания заказа: {e}")
            return 0
    
    def get_player_active_orders(self, player_id: int) -> List[Tuple]:
        """Получить активные заказы игрока"""
        return self.fetch_all('''
            SELECT po.id, ot.name, ot.description, po.started_at, po.deadline, 
                   po.status, po.quality, po.reward
            FROM player_orders po
            JOIN order_templates ot ON po.template_id = ot.id
            WHERE po.player_id = ? AND po.status = 'active'
            ORDER BY po.deadline
        ''', (player_id,))
    
    def get_order_details(self, order_id: int) -> Optional[Tuple]:
        """Получить детальную информацию о заказе"""
        return self.fetch_one('''
            SELECT po.*, ot.name, ot.description, ot.required_items, ot.required_tools,
                   ot.difficulty, ot.category
            FROM player_orders po
            JOIN order_templates ot ON po.template_id = ot.id
            WHERE po.id = ?
        ''', (order_id,))
    
    def complete_order(self, order_id: int, quality: int, used_items: Dict, used_tools: Dict) -> bool:
        """Завершить заказ с указанием качества и использованных предметов"""
        try:
            # Получаем информацию о заказе
            order = self.get_order_details(order_id)
            if not order:
                return False
            
            base_reward = order[17]  # base_reward из шаблона
            difficulty = order[18]   # difficulty из шаблона
            
            # Расчет награды на основе качества и сложности
            quality_bonus = (quality / 100.0) * base_reward
            difficulty_bonus = (difficulty * 0.1) * base_reward
            final_reward = int(base_reward + quality_bonus + difficulty_bonus)
            
            # Расчет удовлетворенности клиента
            client_satisfaction = min(100, quality + (difficulty * 10))
            
            self.execute_query('''
                UPDATE player_orders 
                SET status = 'completed', 
                    quality = ?,
                    reward = ?,
                    completed_at = CURRENT_TIMESTAMP,
                    used_items = ?,
                    used_tools = ?,
                    client_satisfaction = ?
                WHERE id = ?
            ''', (quality, final_reward, json.dumps(used_items), json.dumps(used_tools), client_satisfaction, order_id))
            
            print(f"✅ Заказ {order_id} завершен с качеством {quality}%, награда: {final_reward}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка завершения заказа: {e}")
            return False
    
    def fail_order(self, order_id: int) -> bool:
        """Пометить заказ как проваленный"""
        try:
            self.execute_query(
                "UPDATE player_orders SET status = 'failed', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (order_id,)
            )
            print(f"❌ Заказ {order_id} провален")
            return True
        except Exception as e:
            print(f"❌ Ошибка отметки провала заказа: {e}")
            return False
    
    def cancel_order(self, order_id: int) -> bool:
        """Отменить заказ"""
        try:
            self.execute_query(
                "UPDATE player_orders SET status = 'cancelled', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (order_id,)
            )
            print(f"⚠️ Заказ {order_id} отменен")
            return True
        except Exception as e:
            print(f"❌ Ошибка отмены заказа: {e}")
            return False
    
    def get_player_order_history(self, player_id: int, limit: int = 10) -> List[Tuple]:
        """Получить историю заказов игрока"""
        return self.fetch_all('''
            SELECT po.id, ot.name, po.status, po.quality, po.reward, po.completed_at
            FROM player_orders po
            JOIN order_templates ot ON po.template_id = ot.id
            WHERE po.player_id = ? AND po.status IN ('completed', 'failed', 'cancelled')
            ORDER BY po.completed_at DESC
            LIMIT ?
        ''', (player_id, limit))
    
    def get_player_order_stats(self, player_id: int) -> Dict[str, Any]:
        """Получить статистику заказов игрока"""
        stats = {}
        
        # Общая статистика
        total_stats = self.fetch_one('''
            SELECT 
                COUNT(*) as total_orders,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                AVG(CASE WHEN status = 'completed' THEN quality ELSE NULL END) as avg_quality,
                SUM(CASE WHEN status = 'completed' THEN reward ELSE 0 END) as total_earned
            FROM player_orders 
            WHERE player_id = ?
        ''', (player_id,))
        
        if total_stats:
            stats = {
                "total_orders": total_stats[0] or 0,
                "completed": total_stats[1] or 0,
                "failed": total_stats[2] or 0,
                "cancelled": total_stats[3] or 0,
                "success_rate": (total_stats[1] / total_stats[0] * 100) if total_stats[0] > 0 else 0,
                "avg_quality": total_stats[4] or 0,
                "total_earned": total_stats[5] or 0
            }
        
        return stats
    
    def check_expired_orders(self) -> List[Tuple]:
        """Проверить и получить список просроченных заказов"""
        return self.fetch_all('''
            SELECT po.id, po.player_id, ot.name
            FROM player_orders po
            JOIN order_templates ot ON po.template_id = ot.id
            WHERE po.status = 'active' AND po.deadline < CURRENT_TIMESTAMP
        ''')
    
    def add_custom_order(self, name: str, description: str, required_level: int, difficulty: int, 
                        base_reward: int, required_items: Dict, required_tools: Dict, 
                        time_limit: int, category: str) -> int:
        """Добавить пользовательский заказ"""
        try:
            cursor = self.execute_query('''
                INSERT INTO order_templates (name, description, required_level, difficulty, base_reward,
                                           required_items, required_tools, time_limit, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, description, required_level, difficulty, base_reward,
                 json.dumps(required_items), json.dumps(required_tools), time_limit, category))
            
            order_id = cursor.lastrowid
            print(f"✅ Добавлен пользовательский заказ: {name} (ID: {order_id})")
            return order_id
            
        except Exception as e:
            print(f"❌ Ошибка добавления заказа: {e}")
            return 0
    
    def init_default_clients(self):
        """Инициализация стандартных клиентов"""
        existing_clients = self.fetch_all("SELECT COUNT(*) FROM clients")
        if existing_clients[0][0] > 0:
            return
        
        default_clients = [
            {
                "name": "Алексей Петров",
                "preferences": '{"качество": 80, "скорость": 20, "цена": 60}',
                "base_reputation": 10,
                "favorite_category": "ремни"
            },
            {
                "name": "Мария Иванова", 
                "preferences": '{"качество": 90, "скорость": 40, "цена": 30}',
                "base_reputation": 15,
                "favorite_category": "аксессуары"
            },
            {
                "name": "Дмитрий Соколов",
                "preferences": '{"качество": 70, "скорость": 80, "цена": 50}',
                "base_reputation": 5,
                "favorite_category": "ремни"
            }
        ]
        
        for client in default_clients:
            self.execute_query('''
                INSERT INTO clients (name, preferences, base_reputation, favorite_category)
                VALUES (?, ?, ?, ?)
            ''', (client["name"], client["preferences"], client["base_reputation"], client["favorite_category"]))
        
        print(f"✅ Добавлено {len(default_clients)} стандартных клиентов")