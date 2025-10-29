# database/models.py
import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path='game.db'):
        self.db_path = db_path
        self.init_db()
        self.add_gender_column()
    
    def add_gender_column(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('ALTER TABLE players ADD COLUMN gender TEXT NOT NULL DEFAULT "male"')
            print("✅ Добавлено поле gender в таблицу players")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e):
                raise e
            print(f"✅ Поле gender уже существует или ошибка: {e}")
        finally:
            conn.close()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей Telegram
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица игровых персонажей (ОБНОВЛЕНА - добавлены coins)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                class TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                mastery INTEGER DEFAULT 0,
                luck INTEGER DEFAULT 0,
                marketing INTEGER DEFAULT 0,
                reputation INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 2000,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                gender TEXT NOT NULL DEFAULT 'male',
                FOREIGN KEY (user_id) REFERENCES users (id)               
            )
        ''')
        
        # Таблица инструментов (НОВАЯ)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL,
                mastery_bonus INTEGER DEFAULT 0,
                luck_bonus INTEGER DEFAULT 0,
                durability INTEGER DEFAULT 10
            )
        ''')
        
        # Таблица материалов (НОВАЯ)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price INTEGER NOT NULL,
                stage1_bonus INTEGER DEFAULT 0,
                stage4_bonus INTEGER DEFAULT 0,
                durability INTEGER DEFAULT 1
            )
        ''')
        
        # Таблица инвентаря игрока (НОВАЯ)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                current_durability INTEGER,
                FOREIGN KEY (player_id) REFERENCES players (id)
            )
        ''')
        
        # Наполняем таблицы инструментов и материалов
        self._populate_tools_and_materials(cursor)
        
        conn.commit()
        conn.close()
    
    def _populate_tools_and_materials(self, cursor):
        """Наполняет таблицы инструментов и материалов"""
        # Проверяем, есть ли уже данные
        cursor.execute("SELECT COUNT(*) FROM tools")
        if cursor.fetchone()[0] == 0:
            tools = [
                # Дешевые инструменты
                ("Канцелярский нож", "Ножи", 300, -5, -5, 10),
                ("Высечные пробойники", "Пробойники", 280, 0, 0, 10),
                ("Мультитул 3 в 1", "Торцбилы", 250, -10, -20, 10),
                ("Сликер", "Сликеры", 200, 0, 0, 10),
                # Средние инструменты  
                ("Нож SDI", "Ножи", 900, 10, 5, 15),
                ("Пробойники Wuta", "Пробойники", 840, 0, 0, 18),
                ("Торцбил Wuta", "Торцбилы", 750, 0, -5, 20),
                # Дорогие инструменты
                ("Шорный нож", "Ножи", 3600, 20, 10, 25),
                ("Пробойники Sinabroks", "Пробойники", 3360, 10, 10, 28),
                ("Профессиональный торцбил", "Торцбилы", 3000, 15, 10, 30)
            ]
            
            for tool in tools:
                cursor.execute('''
                    INSERT INTO tools (name, category, price, mastery_bonus, luck_bonus, durability)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', tool)
        
        cursor.execute("SELECT COUNT(*) FROM materials")
        if cursor.fetchone()[0] == 0:
            materials = [
                # Дешевые материалы
                ("Дешевая ременная лента", "Кожа для ремней", 150, -5, -5, 1),
                ("Дешевая фурнитура", "Фурнитура для ремней", 100, -5, -5, 1),
                ("Пчелиный воск", "Химия", 80, 0, -25, 50),
                # Средние материалы
                ("Обычная ременная лента", "Кожа для ремней", 450, 0, 0, 1),
                ("Нержавейка", "Фурнитура для ремней", 300, 0, 0, 1),
                ("Масловосковые смеси", "Химия", 240, 0, -10, 75),
                # Дорогие материалы
                ("Дорогая ременная лента", "Кожа для ремней", 1800, 8, 8, 1),
                ("Латунная фурнитура", "Фурнитура для ремней", 1200, 8, 8, 1),
                ("Профессиональная косметика", "Химия", 960, 0, 30, 100)
            ]
            
            for material in materials:
                cursor.execute('''
                    INSERT INTO materials (name, category, price, stage1_bonus, stage4_bonus, durability)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', material)

    def get_user_players(self, telegram_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.* FROM players p 
            JOIN users u ON p.user_id = u.id 
            WHERE u.telegram_id = ? AND p.is_active = TRUE
        ''', (telegram_id,))
        
        players = cursor.fetchall()
        conn.close()
        return players

    def add_user(self, telegram_id, username, first_name, last_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, username, first_name, last_name))
            
            conn.commit()
            user_id = cursor.lastrowid
            
            # Если пользователь уже существовал, получаем его ID
            if user_id == 0:
                cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
                user_id = cursor.fetchone()[0]
                
        except Exception as e:
            print(f"Error adding user: {e}")
            user_id = None
        finally:
            conn.close()
        
        return user_id

    def add_player(self, user_id, name, player_class, gender='male'):
        """Добавляет нового персонажа с характеристиками по классу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Устанавливаем характеристики в зависимости от класса (ОБНОВЛЕННЫЕ)
        if player_class == "Работяга":
            mastery, luck, marketing, reputation = 25, 15, 5, 5
        elif player_class == "Менеджер":
            mastery, luck, marketing, reputation = 10, 15, 25, 10
        elif player_class == "Блоггер":
            mastery, luck, marketing, reputation = 5, 25, 20, 20
        else:
            mastery, luck, marketing, reputation = 10, 10, 10, 10
        
        try:
            # Деактивируем всех предыдущих персонажей пользователя
            cursor.execute('''
                UPDATE players SET is_active = FALSE 
                WHERE user_id = ?
            ''', (user_id,))
            
            # Создаем нового активного персонажа
            cursor.execute('''
                INSERT INTO players (user_id, name, class, mastery, luck, marketing, reputation, coins, is_active, gender)
                VALUES (?, ?, ?, ?, ?, ?, ?, 2000, TRUE, ?)
            ''', (user_id, name, player_class, mastery, luck, marketing, reputation, gender))
            
            conn.commit()
            player_id = cursor.lastrowid
            
        except Exception as e:
            print(f"Error adding player: {e}")
            player_id = None
        finally:
            conn.close()
        
        return player_id

    def get_active_player(self, telegram_id):
        """Получает активного персонажа пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.* FROM players p 
            JOIN users u ON p.user_id = u.id 
            WHERE u.telegram_id = ? AND p.is_active = TRUE
        ''', (telegram_id,))
        
        player = cursor.fetchone()
        conn.close()
        return player

    def deactivate_player(self, player_id):
        """Деактивирует персонажа"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE players SET is_active = FALSE 
            WHERE id = ?
        ''', (player_id,))
        
        conn.commit()
        conn.close()

    def get_user_by_telegram_id(self, telegram_id):
        """Получает пользователя по telegram_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM users WHERE telegram_id = ?
        ''', (telegram_id,))
        
        user = cursor.fetchone()
        conn.close()
        return user
    
    # Новые методы для работы с инструментами и материалами
    def get_tools_by_category(self, category):
        """Получить инструменты по категории"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tools WHERE category = ? ORDER BY price", (category,))
        tools = cursor.fetchall()
        conn.close()
        return tools
    
    def get_materials_by_category(self, category):
        """Получить материалы по категории"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM materials WHERE category = ? ORDER BY price", (category,))
        materials = cursor.fetchall()
        conn.close()
        return materials
    
    def add_to_inventory(self, player_id, item_type, item_id):
        """Добавить предмет в инвентарь игрока"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Получаем прочность предмета
        if item_type == 'tool':
            cursor.execute("SELECT durability FROM tools WHERE id = ?", (item_id,))
        else:
            cursor.execute("SELECT durability FROM materials WHERE id = ?", (item_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
            
        durability = result[0]
        
        cursor.execute('''
            INSERT INTO player_inventory (player_id, item_type, item_id, current_durability)
            VALUES (?, ?, ?, ?)
        ''', (player_id, item_type, item_id, durability))
        
        conn.commit()
        conn.close()
        return True
    
    def get_player_inventory(self, player_id):
        """Получить инвентарь игрока"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pi.*, 
                   CASE 
                       WHEN pi.item_type = 'tool' THEN t.name
                       WHEN pi.item_type = 'material' THEN m.name
                   END as item_name,
                   CASE 
                       WHEN pi.item_type = 'tool' THEN t.category
                       WHEN pi.item_type = 'material' THEN m.category
                   END as item_category
            FROM player_inventory pi
            LEFT JOIN tools t ON pi.item_type = 'tool' AND pi.item_id = t.id
            LEFT JOIN materials m ON pi.item_type = 'material' AND pi.item_id = m.id
            WHERE pi.player_id = ?
        ''', (player_id,))
        
        inventory = cursor.fetchall()
        conn.close()
        return inventory

class TutorialDatabase:
    def __init__(self):
        # УБИРАЕМ постоянное соединение, создаем при каждом вызове
        self.db_path = 'game.db'
        self.create_tables()
    
    def get_connection(self):
        """Создает новое соединение для каждого запроса"""
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def create_tables(self):
        """Создает таблицы при инициализации"""
        conn = self.get_connection()
        try:
            # Таблица прогресса обучения
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tutorial_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL,
                    current_step TEXT DEFAULT 'start',
                    has_started BOOLEAN DEFAULT FALSE,
                    completed_steps TEXT DEFAULT '',
                    player_balance INTEGER DEFAULT 2000,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES players (id)
                )
            ''')
            
            # Таблица инвентаря обучения
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tutorial_inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL,
                    item_name TEXT,
                    item_type TEXT,
                    quantity INTEGER DEFAULT 1,
                    FOREIGN KEY (player_id) REFERENCES players (id)
                )
            ''')
            
            # Таблица товаров магазина
            conn.execute('''
                CREATE TABLE IF NOT EXISTS shop_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    category TEXT,
                    price INTEGER,
                    available_in_tutorial BOOLEAN DEFAULT FALSE,
                    image_path TEXT
                )
            ''')
            
            conn.commit()
        finally:
            conn.close()
    
    def init_tutorial_progress(self, player_id):
        """Инициализирует прогресс обучения для персонажа"""
        conn = self.get_connection()
        try:
            # Удаляем старый прогресс если есть
            conn.execute('DELETE FROM tutorial_progress WHERE player_id = ?', (player_id,))
            conn.execute('DELETE FROM tutorial_inventory WHERE player_id = ?', (player_id,))
            
            # Создаем новый прогресс
            conn.execute(
                'INSERT INTO tutorial_progress (player_id, player_balance) VALUES (?, ?)',
                (player_id, 2000)
            )
            conn.commit()
        finally:
            conn.close()
    
    def get_tutorial_progress(self, player_id):
        """Получает текущий прогресс обучения"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT current_step, has_started, completed_steps, player_balance FROM tutorial_progress WHERE player_id = ?',
                (player_id,)
            )
            return cursor.fetchone()
        finally:
            conn.close()
    
    def update_tutorial_progress(self, player_id, current_step, completed_step=None):
        """Обновляет прогресс обучения"""
        conn = self.get_connection()
        try:
            if completed_step:
                cursor = conn.execute(
                    'SELECT completed_steps FROM tutorial_progress WHERE player_id = ?',
                    (player_id,)
                )
                result = cursor.fetchone()
                completed_steps = result[0] + ',' + completed_step if result and result[0] else completed_step
                
                conn.execute(
                    'UPDATE tutorial_progress SET current_step = ?, completed_steps = ?, has_started = TRUE WHERE player_id = ?',
                    (current_step, completed_steps, player_id)
                )
            else:
                conn.execute(
                    'UPDATE tutorial_progress SET current_step = ?, has_started = TRUE WHERE player_id = ?',
                    (current_step, player_id)
                )
            conn.commit()
        finally:
            conn.close()
    
    def update_player_balance(self, player_id, new_balance):
        """Обновляет баланс игрока"""
        conn = self.get_connection()
        try:
            conn.execute(
                'UPDATE tutorial_progress SET player_balance = ? WHERE player_id = ?',
                (new_balance, player_id)
            )
            conn.commit()
        finally:
            conn.close()
    
    def add_to_tutorial_inventory(self, player_id, item_name, item_type):
        """Добавляет предмет в инвентарь обучения"""
        conn = self.get_connection()
        try:
            # Проверяем, нет ли уже такого предмета
            cursor = conn.execute(
                'SELECT id FROM tutorial_inventory WHERE player_id = ? AND item_name = ?',
                (player_id, item_name)
            )
            if cursor.fetchone():
                return False  # Предмет уже есть
            
            conn.execute(
                'INSERT INTO tutorial_inventory (player_id, item_name, item_type) VALUES (?, ?, ?)',
                (player_id, item_name, item_type)
            )
            conn.commit()
            return True
        finally:
            conn.close()
    
    def get_tutorial_inventory(self, player_id):
        """Получает инвентарь обучения"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT item_name, item_type, quantity FROM tutorial_inventory WHERE player_id = ?',
                (player_id,)
            )
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_tutorial_inventory_count(self, player_id):
        """Получает количество предметов в инвентаре"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                'SELECT COUNT(*) FROM tutorial_inventory WHERE player_id = ?',
                (player_id,)
            )
            return cursor.fetchone()[0]
        finally:
            conn.close()
    
    def clear_tutorial_data(self, player_id):
        """Очищает все данные обучения для персонажа"""
        conn = self.get_connection()
        try:
            conn.execute('DELETE FROM tutorial_progress WHERE player_id = ?', (player_id,))
            conn.execute('DELETE FROM tutorial_inventory WHERE player_id = ?', (player_id,))
            conn.commit()
        finally:
            conn.close()
    
    def init_shop_items(self):
        """Инициализирует товары магазина с новыми ценами"""
        shop_items = [
            # Ножи (дешевые, средние, дорогие)
            ('Канцелярский нож', 'Ножи', 300, True, 'images/shop/knife_cheap.jpg'),
            ('Нож SDI', 'Ножи', 900, False, 'images/shop/knife_mid.jpg'),
            ('Шорный нож', 'Ножи', 3600, False, 'images/shop/knife_pro.jpg'),
            
            # Нитки
            ('Швейные МосНитки', 'Нитки', 150, True, 'images/shop/threads_cheap.jpg'),
            ('Синтетические нитки', 'Нитки', 450, False, 'images/shop/threads_mid.jpg'),
            ('Льняные нитки', 'Нитки', 1800, False, 'images/shop/threads_pro.jpg'),
            
            # Пробойники
            ('Строчные пробойники PFG', 'Пробойники', 200, False, 'images/shop/punch_line_PFG.jpg'),
            ('Высечные пробойники', 'Пробойники', 280, True, 'images/shop/punch_set.jpg'),
            ('Пробойники Wuta', 'Пробойники', 840, False, 'images/shop/punch_wuta.jpg'),
            ('Пробойники Sinabroks', 'Пробойники', 3360, False, 'images/shop/punch_storybrook.jpg'),
        
            # Торцбилы
            ('Мультитул 3 в 1', 'Торцбилы', 250, True, 'images/shop/edge_slicker.jpg'),
            ('Торцбил Wuta', 'Торцбилы', 750, False, 'images/shop/edge_wuta.jpg'),
            ('Профессиональный торцбил', 'Торцбилы', 3000, False, 'images/shop/edge_pro.jpg'),
        
            # Материалы (кожа)
            ('Дешевая ременная заготовка', 'Материалы', 150, True, 'images/shop/leather_cheap.jpg'),
            ('Обычная ременная заготовка', 'Материалы', 450, False, 'images/shop/leather_mid.jpg'),
            ('Дорогая ременная заготовка', 'Материалы', 1800, False, 'images/shop/leather_expensive.jpg'),
            ("Кожа для галантереи (дешевая)", 'Материалы', 200, False, "images/shop/leather_galanterey_cheap.jpg"),
            ("Кожа для галантереи (средняя)", 'Материалы', 600, False, "images/shop/leather_galanterey_mid.jpg"), 
            ("Кожа для галантереи (дорогая)", 'Материалы', 2400, False, "images/shop/leather_galanterey_pro.jpg"),
            ("Кожа для сумок (дешевая)", 'Материалы', 400, False, "images/shop/leather_bags_cheap.jpg"),
            ("Кожа для сумок (средняя)", 'Материалы', 1200, False, "images/shop/leather_bags_mid.jpg"),
            ("Кожа для сумок (дорогая)", 'Материалы', 4800, False, "images/shop/leather_bags_pro.jpg"),
            
            # Фурнитура
            ('Дешевая фурнитура для ремней', 'Фурнитура', 100, True, 'images/shop/hardware_belts.jpg'),
            ('Нержавейка для ремней', 'Фурнитура', 300, False, 'images/shop/hardware_wallets.jpg'),
            ('Латунная фурнитура для ремней', 'Фурнитура', 1200, False, 'images/shop/hardware_bags.jpg'),
            ('Дешевая фурнитура для сумок', 'Фурнитура', 150, False, 'images/shop/hardware_bags_cheap.jpg'),
            ('Средняя фурнитура для сумок', 'Фурнитура', 450, False, 'images/shop/hardware_bags_mid.jpg'),
            ('Дорогая фурнитура для сумок', 'Фурнитура', 1800, False, 'images/shop/hardware_bags_pro.jpg'),
        
             # Химия
            ('Пчелиный воск', 'Химия', 80, True, 'images/shop/wax.jpg'),
            ('Масловосковые смеси', 'Химия', 240, False, 'images/shop/wax_mix.jpg'),
            ('Профессиональная косметика', 'Химия', 960, False, 'images/shop/pro_cosmetics.jpg'),
        ]
        
        conn = self.get_connection()
        try:
            # Очищаем и заполняем заново
            conn.execute('DELETE FROM shop_items')
            for item in shop_items:
                conn.execute(
                    'INSERT INTO shop_items (name, category, price, available_in_tutorial, image_path) VALUES (?, ?, ?, ?, ?)',
                    item
                )
            conn.commit()
        finally:
            conn.close()
    
    def get_shop_items_by_category(self, category=None, tutorial_only=False):
        """Получает товары магазина"""
        conn = self.get_connection()
        try:
            if category:
                if tutorial_only:
                    cursor = conn.execute(
                        'SELECT name, price, available_in_tutorial, image_path FROM shop_items WHERE category = ? AND available_in_tutorial = TRUE ORDER BY price',
                        (category,)
                    )
                else:
                    cursor = conn.execute(
                        'SELECT name, price, available_in_tutorial, image_path FROM shop_items WHERE category = ? ORDER BY price',
                        (category,)
                    )
            else:
                cursor = conn.execute(
                    'SELECT name, category, price, available_in_tutorial, image_path FROM shop_items ORDER BY category, price'
                )
            return cursor.fetchall()
        finally:
            conn.close()

# Создаем экземпляр базы данных для обучения
tutorial_db = TutorialDatabase()