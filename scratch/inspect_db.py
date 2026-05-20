import sqlite3

conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

# Get Lotti_Interni schema
print("=== SCHEMA LOTTI_INTERNI ===")
res = cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='Lotti_Interni'").fetchone()
if res:
    print(res[0])

# Get column names
print("\n=== COLUMNS LOTTI_INTERNI ===")
cursor.execute("PRAGMA table_info(Lotti_Interni)")
cols = cursor.fetchall()
for col in cols:
    print(col)

# Get sample row
print("\n=== SAMPLE ROW LOTTI_INTERNI ===")
cursor.execute("SELECT * FROM Lotti_Interni LIMIT 1")
row = cursor.fetchone()
if row:
    desc = [d[0] for d in cursor.description]
    for k, v in zip(desc, row):
        print(f"{k}: {v} ({type(v).__name__})")
else:
    print("No rows found in Lotti_Interni")

# Get some statistics on giacenza
print("\n=== GIACENZA STATS ===")
cursor.execute("SELECT lotto_interno, codice_mp, giacenza, data_arrivo, data_scadenza FROM Lotti_Interni LIMIT 5")
for r in cursor.fetchall():
    print(r)

# See how many MP have low stock or scorta_minima
print("\n=== SCORTA MINIMA STATS ===")
cursor.execute("SELECT codice, nome_mp, scorta_minima FROM Elenco_MP LIMIT 5")
for r in cursor.fetchall():
    print(r)

conn.close()
