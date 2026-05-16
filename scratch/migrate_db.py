import sqlite3
import os

DB_PATH = os.path.join("database", "database.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    print("Aggiunta colonna scorta_minima...")
    cursor.execute("ALTER TABLE Elenco_MP ADD COLUMN scorta_minima FLOAT DEFAULT 0")
except sqlite3.OperationalError:
    print("Colonna scorta_minima già esistente o errore.")

try:
    print("Aggiunta colonna ordine_magazzino...")
    cursor.execute("ALTER TABLE Elenco_MP ADD COLUMN ordine_magazzino INTEGER DEFAULT 999")
except sqlite3.OperationalError:
    print("Colonna ordine_magazzino già esistente o errore.")

try:
    print("Aggiunta colonna categoria_magazzino...")
    cursor.execute("ALTER TABLE Elenco_MP ADD COLUMN categoria_magazzino TEXT")
except sqlite3.OperationalError:
    print("Colonna categoria_magazzino già esistente o errore.")

conn.commit()
conn.close()
print("Migrazione completata.")
