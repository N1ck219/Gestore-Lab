import sqlite3
import os

db_path = os.path.join("database", "database.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(Lotti_Interni);")
columns = cursor.fetchall()
for col in columns:
    print(col)
conn.close()
