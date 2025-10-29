"""
Управление персонажами игроков - создание, характеристики, прогресс
"""

import sqlite3
from typing import List, Tuple, Optional, Dict, Any
from .models import BaseDatabase


class CharactersDB(BaseDatabase):
    """
    Управление персонажами игроков
    Создание, характеристики, уровни, классы
    """
    
    def __init__(self, db_path: str = "game.db"):
        super().__init__(db_path)
        self._ensure_character_tables()
    
    def _ensure_character_tables(self):
        """Создает таблицы персонажей если не существуют"""
        # Таблица пользователей Telegram
        users_query = '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        self.execute_query(users_query)
        
        # Таблица игровых персонажей
        players_query = '''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                class TEXT NOT NULL,
                mastery INTEGER DEFAULT 0,
                luck INTEGER DEFAULT 0,
                marketing INTEGER DEFAULT 0,
                reputation INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 1500,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, name)
            )
        '''
        self.execute_query(players_query)
        print("🎯 Таблицы users и players созданы/проверены")
    
    def get_or_create_user(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None) -> int:
        """
        Получить существующего пользователя или создать нового
        Возвращает user_id
        """
        # Пытаемся найти существующего пользователя
        user = self.fetch_one(
            "SELECT id FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        
        if user:
            return user[0]
        
        # Создаем нового пользователя
        try:
            cursor = self.execute_query(
                "INSERT INTO users (telegram_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                (telegram_id, username, first_name, last_name)
            )
            print(f"✅ Создан новый пользователь: {telegram_id}")
            return cursor.lastrowid
        except Exception as e:
            print(f"❌ Ошибка создания пользователя: {e}")
            return 0
    
    def add_player(self, user_id: int, name: str, player_class: str) -> int:
        """
        Создать нового персонажа
        Возвращает player_id или 0 при ошибке
        """
        # Деактивируем всех предыдущих персонажей пользователя
        self.execute_query(
            "UPDATE players SET is_active = FALSE WHERE user_id = ?",
            (user_id,)
        )
        
        # Устанавливаем стартовые характеристики по классу
        stats = self._get_starting_stats(player_class)
        
        try:
            cursor = self.execute_query('''
                INSERT INTO players (user_id, name, class, mastery, luck, marketing, reputation, coins, level, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, TRUE)
            ''', (user_id, name, player_class, stats['mastery'], stats['luck'], stats['marketing'], stats['reputation'], stats['coins']))
            
            player_id = cursor.lastrowid
            print(f"✅ Создан персонаж '{name}' (класс: {player_class}) с ID {player_id}")
            return player_id
            
        except Exception as e:
            print(f"❌ Ошибка создания персонажа: {e}")
            return 0
    
    def _get_starting_stats(self, player_class: str) -> Dict[str, int]:
        """Получить стартовые характеристики по классу"""
        stats = {
            "Работяга": {"mastery": 25, "luck": 15, "marketing": 5, "reputation": 5, "coins": 1500},
            "Менеджер": {"mastery": 10, "luck": 15, "marketing": 25, "reputation": 10, "coins": 1500},
            "Блоггер": {"mastery": 5, "luck": 25, "marketing": 20, "reputation": 20, "coins": 1500}
        }
        return stats.get(player_class, stats["Работяга"])
    
    def get_active_player(self, telegram_id: int) -> Optional[Tuple]:
        """
        Получить активного персонажа пользователя
        Возвращает кортеж с данными персонажа
        """
        query = '''
            SELECT p.id, p.name, p.class, p.mastery, p.luck, p.marketing, p.reputation, 
                   p.coins, p.level, p.experience, p.user_id
            FROM players p
            JOIN users u ON p.user_id = u.id
            WHERE u.telegram_id = ? AND p.is_active = TRUE
        '''
        return self.fetch_one(query, (telegram_id,))
    
    def get_player_by_id(self, player_id: int) -> Optional[Tuple]:
        """Получить персонажа по ID"""
        return self.fetch_one(
            "SELECT id, name, class, mastery, luck, marketing, reputation, coins, level, experience, user_id FROM players WHERE id = ?",
            (player_id,)
        )
    
    def update_player_stats(self, player_id: int, stats: Dict[str, int]) -> bool:
        """Обновить характеристики персонажа"""
        try:
            query = "UPDATE players SET "
            params = []
            
            for stat, value in stats.items():
                if stat in ['mastery', 'luck', 'marketing', 'reputation', 'coins', 'level', 'experience']:
                    query += f"{stat} = ?, "
                    params.append(value)
            
            query = query.rstrip(", ") + " WHERE id = ?"
            params.append(player_id)
            
            self.execute_query(query, tuple(params))
            print(f"✅ Характеристики персонажа {player_id} обновлены")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления характеристик: {e}")
            return False
    
    def add_experience(self, player_id: int, exp: int) -> bool:
        """Добавить опыт персонажу"""
        try:
            # Получаем текущий опыт
            player = self.get_player_by_id(player_id)
            if not player:
                return False
            
            current_exp = player[9]  # experience
            new_exp = current_exp + exp
            
            # Проверяем повышение уровня
            current_level = player[8]  # level
            new_level = self._calculate_level(new_exp)
            
            if new_level > current_level:
                # Повышаем уровень
                self.execute_query(
                    "UPDATE players SET experience = ?, level = ? WHERE id = ?",
                    (new_exp, new_level, player_id)
                )
                print(f"🎉 Персонаж {player_id} повысил уровень до {new_level}!")
                return True
            else:
                # Только добавляем опыт
                self.execute_query(
                    "UPDATE players SET experience = ? WHERE id = ?",
                    (new_exp, player_id)
                )
                return True
                
        except Exception as e:
            print(f"❌ Ошибка добавления опыта: {e}")
            return False
    
    def _calculate_level(self, experience: int) -> int:
        """Рассчитать уровень на основе опыта"""
        # Простая формула: каждый уровень требует 100 опыта
        return max(1, experience // 100)
    
    def update_coins(self, player_id: int, coins_change: int) -> bool:
        """Обновить баланс монет персонажа"""
        try:
            player = self.get_player_by_id(player_id)
            if not player:
                return False
            
            current_coins = player[7]  # coins
            new_coins = max(0, current_coins + coins_change)  # Не может быть отрицательным
            
            self.execute_query(
                "UPDATE players SET coins = ? WHERE id = ?",
                (new_coins, player_id)
            )
            print(f"💰 Баланс персонажа {player_id}: {current_coins} -> {new_coins} (изменение: {coins_change})")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления баланса: {e}")
            return False
    
    def get_player_characteristics(self, player_id: int) -> Dict[str, Any]:
        """Получить полные характеристики персонажа"""
        player = self.get_player_by_id(player_id)
        if not player:
            return {}
        
        return {
            "id": player[0],
            "name": player[1],
            "class": player[2],
            "mastery": player[3],
            "luck": player[4],
            "marketing": player[5],
            "reputation": player[6],
            "coins": player[7],
            "level": player[8],
            "experience": player[9],
            "user_id": player[10]
        }
    
    def get_all_player_characters(self, telegram_id: int) -> List[Tuple]:
        """Получить всех персонажей пользователя"""
        query = '''
            SELECT p.id, p.name, p.class, p.level, p.is_active
            FROM players p
            JOIN users u ON p.user_id = u.id
            WHERE u.telegram_id = ?
            ORDER BY p.is_active DESC, p.created_at DESC
        '''
        return self.fetch_all(query, (telegram_id,))
    
    def switch_active_character(self, telegram_id: int, character_id: int) -> bool:
        """Сменить активного персонажа"""
        try:
            # Получаем user_id
            user = self.fetch_one("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            if not user:
                return False
            
            user_id = user[0]
            
            # Деактивируем всех персонажей пользователя
            self.execute_query(
                "UPDATE players SET is_active = FALSE WHERE user_id = ?",
                (user_id,)
            )
            
            # Активируем выбранного персонажа
            self.execute_query(
                "UPDATE players SET is_active = TRUE WHERE id = ? AND user_id = ?",
                (character_id, user_id)
            )
            
            print(f"✅ Активный персонаж изменен на {character_id} для пользователя {telegram_id}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка смены персонажа: {e}")
            return False