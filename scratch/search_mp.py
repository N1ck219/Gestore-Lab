import sqlite3
import os

DB_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
search_terms = ['TSA', 'Capsule', 'FDG', '18O', 'Flaconi sterili', 'Kit']
for term in search_terms:
    print(f"--- Search: {term} ---")
    cursor.execute("SELECT codice, nome_mp FROM Elenco_MP WHERE nome_mp LIKE ?", (f'%{term}%',))
    rows = cursor.fetchall()
    for row in rows:
        print(f"{row[0]} | {row[1]}")
conn.close()
