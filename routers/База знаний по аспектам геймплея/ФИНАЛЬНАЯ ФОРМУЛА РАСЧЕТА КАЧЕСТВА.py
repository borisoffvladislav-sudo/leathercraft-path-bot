def calculate_final_result(player_mastery, player_luck, tools_bonus, materials_bonus, order_difficulty):
    # 1. РАСЧЕТ БРАКА
    failure_chance = max(1, 5 - (player_luck / 10))
    is_failure = random.randint(1, 100) <= failure_chance
    if is_failure:
        return "Брак"
    
    # 2. ДИНАМИЧЕСКИЕ ПОРОГИ КАЧЕСТВА
    scaling_factor = player_mastery / 150
    ordinary_threshold = 25 + (order_difficulty * 4) + scaling_factor
    excellent_threshold = 50 + (order_difficulty * 8) + (scaling_factor * 1.5)
    superb_threshold = 75 + (order_difficulty * 12) + (scaling_factor * 2)
    
    # 3. РАСЧЕТ КАЧЕСТВА
    base_quality = (player_mastery * 0.8) + player_luck
    total_bonus = tools_bonus + materials_bonus
    final_quality = base_quality + (base_quality * total_bonus / 100) - (order_difficulty * 6)
    
    # 4. ОПРЕДЕЛЕНИЕ УРОВНЯ КАЧЕСТВА
    if final_quality <= ordinary_threshold:
        return "Обычный"
    elif final_quality <= excellent_threshold:
        return "Отличный" 
    else:
        return "Превосходный"