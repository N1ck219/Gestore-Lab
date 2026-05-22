import sqlite3
import os

DB_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    print("Aggiunta colonna qc_attesa...")
    cursor.execute("ALTER TABLE Lotti_Interni ADD COLUMN qc_attesa TEXT DEFAULT 'NO'")
    conn.commit()
    print("Successo!")
except sqlite3.OperationalError as e:
    print("Colonna qc_attesa già esistente o errore:", e)

conn.close()
print("Migrazione QC completata.")
