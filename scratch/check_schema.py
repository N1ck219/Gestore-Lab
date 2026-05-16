import sqlite3
import os

db_path = os.path.join('database', 'database.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Schema Scarichi:")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Scarichi'")
row = cursor.fetchone()
if row:
    print(row[0])
else:
    print("Table Scarichi not found")

print("\nSchema Lotti_Interni:")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Lotti_Interni'")
row = cursor.fetchone()
if row:
    print(row[0])

conn.close()
