import sqlite3
import os

db_path = os.path.join("database", "database.db")
if not os.path.exists(db_path):
    print("Database does not exist")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables:", [t[0] for t in tables])
    for t in tables:
        table_name = t[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"Table '{table_name}' columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    conn.close()
