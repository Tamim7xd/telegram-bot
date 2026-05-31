from shared.database import get_db

def get_balance(user_id):
    conn = get_db()
    cursor = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result["balance"] if result else 1000

def update_balance(user_id, amount):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_level(user_id):
    conn = get_db()
    cursor = conn.execute("SELECT level, messages FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result["level"], result["messages"]
    return 1, 0

def update_messages(user_id):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.execute("UPDATE users SET messages = messages + 1 WHERE user_id = ?", (user_id,))
    
    cursor = conn.execute("SELECT messages, level FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    messages = result["messages"]
    current_level = result["level"]
    
    from .economy_data import MESSAGE_TO_LEVEL, LEVEL_REWARD
    new_level = (messages // MESSAGE_TO_LEVEL) + 1
    
    if new_level > current_level:
        reward = (new_level - current_level) * LEVEL_REWARD
        conn.execute("UPDATE users SET level = ?, balance = balance + ? WHERE user_id = ?", 
                     (new_level, reward, user_id))
        conn.commit()
        conn.close()
        return True, new_level, reward
    
    conn.commit()
    conn.close()
    return False, current_level, 0