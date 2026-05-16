import sqlite3
import os

db_path = os.path.join('database', 'database.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Columns in Scarichi:")
cursor.execute("PRAGMA table_info(Scarichi)")
rows = cursor.fetchall()
for row in rows:
    print(row[1]) # Name is the second element

conn.close()
