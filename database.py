import sqlite3
import threading
from datetime import datetime

# Безопасное подключение к БД для многих пользователей
class Database:
    def __init__(self):
        self.local = threading.local()
    
    def get_connection(self):
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect("players.db", check_same_thread=False)
            self.local.conn.row_factory = sqlite3.Row  # Чтобы получать данные по имени столбца
        return self.local.conn

# Создаем один экземпляр базы данных
db = Database()

def init_database():
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Таблица игроков
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        character_name TEXT,
        character_type TEXT,
        mastery INTEGER,
        luck INTEGER,
        marketing INTEGER,
        reputation INTEGER,
        title TEXT DEFAULT '',
        coins INTEGER DEFAULT 0,
        last_login TEXT
    )
    """)
    
    # Таблица шаблонов заказов
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        difficulty TEXT,
        required_mastery INTEGER,
        base_coins INTEGER,
        base_exp INTEGER,
        base_rep INTEGER
    )
    """)
    
    # Таблица активных заказов игроков
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS player_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        order_template_id INTEGER,
        status TEXT DEFAULT 'active',
        created_at TEXT,
        completed_at TEXT,
        FOREIGN KEY (user_id) REFERENCES players (user_id),
        FOREIGN KEY (order_template_id) REFERENCES order_templates (id)
    )
    """)
    
    # Наполняем шаблоны заказов
    cursor.execute("SELECT COUNT(*) FROM order_templates")
    if cursor.fetchone()[0] == 0:
        # Добавляем тестовые заказы
        orders = [
            ("Простой ремень", "Изготовить простой кожаный ремень", "easy", 1, 10, 5, 0),
            ("Кошелек", "Создать кожаный кошелек", "easy", 2, 15, 8, 1),
            ("Чехол для телефона", "Изготовить чехол для телефона", "medium", 3, 30, 15, 1),
            ("Портмоне", "Создать кожаное портмоне", "medium", 4, 45, 20, 2),
            ("Сумка", "Изготовить кожаную сумку", "hard", 5, 70, 35, 3)
        ]
        
        for order in orders:
            cursor.execute("""
                INSERT INTO order_templates (name, description, difficulty, required_mastery, base_coins, base_exp, base_rep)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, order)
    
    conn.commit()

# ===== ИГРОКИ =====
def add_player(user_id, character_name, character_type, mastery, luck, marketing, reputation, title="", coins=0):
    conn = db.get_connection()
    cursor = conn.cursor()
    
    username = character_name
    last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT OR REPLACE INTO players (
            user_id, username, character_name, character_type,
            mastery, luck, marketing, reputation, title, coins, last_login
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, username, character_name, character_type,
        mastery, luck, marketing, reputation, title, coins, last_login
    ))
    conn.commit()

def get_player(user_id):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def delete_player(user_id):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM players WHERE user_id = ?", (user_id,))
    conn.commit()

def update_player(user_id, **kwargs):
    """Обновляет данные игрока"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    if not kwargs:
        return
    
    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values())
    values.append(user_id)
    
    cursor.execute(f"UPDATE players SET {set_clause} WHERE user_id = ?", values)
    conn.commit()

# ===== ЗАКАЗЫ =====
def get_available_orders(user_id):
    """Получить заказы доступные для игрока"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    player = get_player(user_id)
    if not player:
        return []
    
    cursor.execute("""
        SELECT * FROM order_templates 
        WHERE required_mastery <= ? 
        ORDER BY required_mastery
    """, (player['mastery'],))
    
    orders = cursor.fetchall()
    return [dict(order) for order in orders]

def accept_order(user_id, order_template_id):
    """Принять заказ в работу"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO player_orders (user_id, order_template_id, created_at)
        VALUES (?, ?, ?)
    """, (user_id, order_template_id, created_at))
    
    conn.commit()
    return cursor.lastrowid

# Инициализируем базу при импорте
init_database()