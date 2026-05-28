c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    messages INTEGER DEFAULT 0,
    money INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    title TEXT DEFAULT 'مبتدئ',
    banned INTEGER DEFAULT 0,
    muted INTEGER DEFAULT 0
)
""")
conn.commit()
