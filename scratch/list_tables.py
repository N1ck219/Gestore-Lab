import sqlite3
import os

db_path = os.path.join("database", "database.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tabelle nel database:")
for t in tables:
    print(f"- {t[0]}")
conn.close()
