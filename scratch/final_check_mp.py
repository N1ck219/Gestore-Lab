import sqlite3
import os

DB_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Searching for the materials we saw in the Excel "Picking FDG"
items_to_find = [
    'Flaconi sterili apirogeni crimpati HUAYI',
    'Capsule sterili HUAYI',
    'Piastre per campionamento microbiologico TSA 55 mm',
    'Piastre per campionamento microbiologico TSA 90 mm',
    'Acqua arricchita [18O]H2O',
    'Etanolo eccipiente',
    'Kit di frazionamento'
]

results = {}
for item in items_to_find:
    cursor.execute("SELECT codice, nome_mp FROM Elenco_MP WHERE nome_mp LIKE ?", (f'%{item}%',))
    row = cursor.fetchone()
    if row:
        results[item] = row[0]
    else:
        # Try a broader search
        cursor.execute("SELECT codice, nome_mp FROM Elenco_MP WHERE nome_mp LIKE ?", (f'%{item.split()[0]}%',))
        rows = cursor.fetchall()
        results[item] = [(r[0], r[1]) for r in rows[:3]]

for item, res in results.items():
    print(f"{item} => {res}")

conn.close()
