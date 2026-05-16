import sqlite3
import os

def clear_database():
    db_path = os.path.join("database", "database.db")
    
    if not os.path.exists(db_path):
        print(f"Errore: Il database non esiste in {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Disabilita i vincoli di foreign key per evitare errori durante lo svuotamento
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # Ottieni tutte le tabelle (escluse quelle di sistema)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()

        if not tables:
            print("Nessuna tabella trovata nel database.")
            return

        print(f"Trovate {len(tables)} tabelle. Inizio svuotamento...")

        for table in tables:
            table_name = table[0]
            print(f"Svuotamento tabella: {table_name}")
            cursor.execute(f"DELETE FROM {table_name};")
            
        # Resetta i contatori auto-increment se esiste la tabella sqlite_sequence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
        if cursor.fetchone():
            print("Reset dei contatori auto-increment...")
            cursor.execute("DELETE FROM sqlite_sequence;")

        conn.commit()
        
        # Riabilita i vincoli di foreign key
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Ottimizza e riduce la dimensione del file
        print("Ottimizzazione database (VACUUM)...")
        cursor.execute("VACUUM;")
        
        conn.close()
        print("\nDatabase svuotato con successo!")

    except sqlite3.Error as e:
        print(f"Errore durante lo svuotamento del database: {e}")

if __name__ == "__main__":
    confirm = input("Sei SICURO di voler svuotare TUTTE le tabelle del database? (s/n): ")
    if confirm.lower() == 's':
        clear_database()
    else:
        print("Operazione annullata.")
