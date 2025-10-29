#!/usr/bin/env python3
"""
Полное исправление start.py для новой архитектуры БД
"""

def fix_start_complete():
    print("🔧 Полное исправление start.py...")
    
    with open('routers/start.py', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 1. Удаляем tutorial_db из импорта
    content = content.replace(
        "from routers.tutorial import (\n    tutorial_db,\n    get_showcase_keyboard,\n    tutorial_router\n)",
        "from routers.tutorial import (\n    get_showcase_keyboard,\n    tutorial_router\n)"
    )
    
    # 2. Заменяем все использования tutorial_db на Database()
    replacements = [
        # В функции create_character
        ("tutorial_db.init_tutorial_progress(player_id)", "db.tutorial.init_tutorial_progress(player_id)"),
        ("tutorial_db.update_player_balance(player_id, 1500)", "db.tutorial.update_player_balance(player_id, 1500)"),
        
        # В других функциях где используется tutorial_db
        ("tutorial_db.", "db.tutorial."),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    # 3. Добавляем создание db в функции где используется tutorial_db
    functions_to_fix = [
        'async def create_character(callback: CallbackQuery, state: FSMContext):',
        'async def confirm_character(callback: CallbackQuery, state: FSMContext):'
    ]
    
    for func_start in functions_to_fix:
        if func_start in content:
            # Находим функцию и добавляем создание db после начала функции
            pattern = rf'({re.escape(func_start)}.*?)(?=    #|\n    |\nasync|\n@)'
            replacement = r'\1\n    from database.models import Database\n    db = Database()\n'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open('routers/start.py', 'w', encoding='utf-8') as file:
        file.write(content)
    
    print("✅ start.py полностью исправлен!")
    print("🚀 Пробуйте запустить бота: python bot.py")

if __name__ == "__main__":
    import re
    fix_start_complete()