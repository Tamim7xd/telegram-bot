from shared.database import get_db
import time

def save_game_result(user_id, game_name, score):
    conn = get_db()
    conn.execute(
        "INSERT INTO game_stats (user_id, game_name, score, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, game_name, score, int(time.time()))
    )
    conn.commit()
    conn.close()