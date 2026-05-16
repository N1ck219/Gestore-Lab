import sqlite3
import os

DB_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM Elenco_MP")
count = cursor.fetchone()[0]
print(f"Total materials: {count}")
cursor.execute("SELECT codice, nome_mp FROM Elenco_MP LIMIT 50")
rows = cursor.fetchall()
for row in rows:
    print(f"{row[0]} | {row[1]}")
conn.close()
