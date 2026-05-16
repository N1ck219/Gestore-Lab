import pandas as pd
import sqlite3
import os

# Configurazione
file_path = r'database\Materie Prime.xlsm'
db_path = r'database\database.db'
sheet_name = 'Elenco MP'
table_name = 'Elenco_MP'

def import_data():
    if not os.path.exists(file_path):
        print(f"Errore: Il file {file_path} non esiste.")
        return

    try:
        # Caricamento dati
        print(f"Caricamento foglio '{sheet_name}'...")
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        
        # Pulizia colonne: prendiamo solo quelle che ci servono e le rinominiamo
        # Usiamo il mapping basato sui nomi attuali (gestendo i caratteri speciali)
        mapping = {
            'Materie prime': 'nome_mp',
            'Codice': 'codice',
            'NomeFile': 'nome_file',
            'Unit': 'unita_misura', # Gestione del carattere speciale visto nel log
            'Nome per etichette': 'nome_etichetta',
            'Uso': 'uso',
            'Codice forn.': 'codice_fornitore',
            'Controcampione': 'controcampione',
            'Distrib.': 'distribuzione'
        }
        
        # Se Unit non viene trovato esattamente, cerchiamo una colonna che inizi con 'Unit'
        if 'Unit' not in df.columns:
            for col in df.columns:
                if col.startswith('Unit'):
                    mapping[col] = 'unita_misura'
                    break

        # Filtriamo il dataframe per le colonne che abbiamo trovato nel mapping
        available_cols = [c for c in mapping.keys() if c in df.columns]
        df = df[available_cols].copy()
        df.rename(columns=mapping, inplace=True)
        
        # Pulizia dati: rimuoviamo righe dove il codice è nullo (non possono essere PK)
        df.dropna(subset=['codice'], inplace=True)
        
        # Convertiamo il codice in stringa e rimuoviamo eventuali spazi
        df['codice'] = df['codice'].astype(str).str.strip()
        
        # Controllo duplicati sul codice
        duplicates = df[df.duplicated('codice')]
        if not duplicates.empty:
            print(f"Attenzione: Trovati {len(duplicates)} codici duplicati. Verrà mantenuta solo la prima occorrenza.")
            df.drop_duplicates('codice', keep='first', inplace=True)

        # Connessione al database
        print(f"Connessione a {db_path}...")
        conn = sqlite3.connect(db_path)
        
        # Inserimento dati
        # Utilizziamo to_sql con if_exists='replace' per creare la tabella con la struttura corretta
        # Nota: Pandas non imposta automaticamente la Primary Key con to_sql in modo nativo per SQLite
        # Quindi creeremo la tabella manualmente prima se vogliamo vincoli forti, 
        # oppure facciamo una query successiva.
        
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        create_table_query = f"""
        CREATE TABLE {table_name} (
            codice TEXT PRIMARY KEY,
            nome_mp TEXT,
            nome_file TEXT,
            unita_misura TEXT,
            nome_etichetta TEXT,
            uso TEXT,
            codice_fornitore TEXT,
            controcampione TEXT,
            distribuzione TEXT,
            scorta_minima FLOAT DEFAULT 0,
            ordine_magazzino INTEGER DEFAULT 999,
            categoria_magazzino TEXT
        )
        """
        cursor.execute(create_table_query)
        
        # Inserimento dei dati
        df.to_sql(table_name, conn, if_exists='append', index=False)
        
        conn.commit()
        print(f"Importazione completata con successo! {len(df)} righe inserite nella tabella '{table_name}'.")
        
        # Verifica finale
        res = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        print(f"Righe verificate nel DB: {res[0]}")
        
        conn.close()

    except Exception as e:
        print(f"Errore durante l'importazione: {e}")

if __name__ == "__main__":
    import_data()
