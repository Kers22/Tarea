import sqlite3
con = sqlite3.connect("bot.db")
cur = con.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        discord_id TEXT PRIMARY KEY,
        name TEXT,
        gmail TEXT NOT NULL,
        password TEXT NOT NULL,
        token TEXT
    )
""")

con.commit()