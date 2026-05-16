import sqlite3
import os

DB_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Mapping from incorrect temp codes (1-15) to correct official codes
mapping = {
    '1': '741',
    '2': '2065',
    '3': '742',
    '4': '740',
    '5': '461',
    '6': '1368',
    '7': '701',
    '8': '4379',
    '9': '4380',
    '10': '605',
    '11': '606',
    '12': '521',
    '13': '3600',
    '14': '4357',
    '15': '424'
}

print("Inizio correzione codici...")

# 1. Disabilita temporaneamente i vincoli (per sicurezza se presenti)
cursor.execute("PRAGMA foreign_keys = OFF")

for old_code, new_code in mapping.items():
    print(f"Aggiornamento {old_code} -> {new_code}")
    
    # Aggiorna Elenco_MP
    cursor.execute("UPDATE Elenco_MP SET codice = ? WHERE codice = ?", (new_code, old_code))
    
    # Aggiorna Lotti_Interni
    cursor.execute("UPDATE Lotti_Interni SET codice_mp = ? WHERE codice_mp = ?", (new_code, old_code))

# 2. Riabilita vincoli
cursor.execute("PRAGMA foreign_keys = ON")

conn.commit()
conn.close()
print("Database aggiornato con successo.")
