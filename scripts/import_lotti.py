import pandas as pd
import sqlite3
import os

# Configurazione
file_path = r'database\Materie Prime.xlsm'
db_path = r'database\database.db'
sheet_name = 'Lotti interni'
table_name = 'Lotti_Interni'

def import_lotti():
    if not os.path.exists(file_path):
        print(f"Errore: Il file {file_path} non esiste.")
        return

    try:
        print(f"Caricamento dati da '{sheet_name}'...")
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        
        # Mapping completo colonne
        mapping = {
            'LOTTO INTERNO': 'lotto_interno',
            'Data arrivo': 'data_arrivo',
            'MATERIALE': 'materiale_nome',
            'Lotto fornitore': 'lotto_fornitore',
            'Fornitori': 'fornitore',
            'Data scadenza': 'data_scadenza',
            'Qnt. Arrivata': 'qnt_arrivata',
            'Pz  x cf': 'pz_x_cf',
            'Giacenza': 'giacenza',
            'Data consegna QC': 'data_consegna_qc',
            'Data approvazione': 'data_approvazione',
            'Arrivo magazzino': 'arrivo_magazzino',
            'Consumi': 'consumi',
            'C.A.': 'ca',
            'Reparto': 'reparto',
            'Appr.': 'appr',
            'Etich.': 'etich',
            'CC': 'cc',
            'COD_lotto': 'codice_lotto',
            'In Uso': 'in_uso',
            'Chiuso': 'chiuso'
        }
        
        available_cols = [c for c in mapping.keys() if c in df.columns]
        df = df[available_cols].copy()
        df.rename(columns=mapping, inplace=True)
        
        # Pulizia righe: lotto_interno è obbligatorio
        df.dropna(subset=['lotto_interno'], inplace=True)
        df['lotto_interno'] = df['lotto_interno'].astype(str).str.strip()
        
        # Connessione al DB
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # SVUOTAMENTO TABELLA (DROP e CREATE per pulizia totale)
        print("Svuotamento tabella esistente...")
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        cursor.execute(f"""
        CREATE TABLE {table_name} (
            lotto_interno TEXT PRIMARY KEY,
            data_arrivo TEXT,
            codice_mp TEXT,
            lotto_fornitore TEXT,
            fornitore TEXT,
            data_scadenza TEXT,
            qnt_arrivata TEXT,
            pz_x_cf TEXT,
            giacenza TEXT,
            data_consegna_qc TEXT,
            data_approvazione TEXT,
            arrivo_magazzino TEXT,
            consumi TEXT,
            ca TEXT,
            reparto TEXT,
            appr TEXT,
            etich TEXT,
            cc TEXT,
            codice_lotto TEXT,
            in_uso TEXT,
            chiuso TEXT,
            FOREIGN KEY (codice_mp) REFERENCES Elenco_MP(codice)
        )
        """)

        # Lookup codici materia prima
        mp_df = pd.read_sql_query("SELECT codice, nome_mp FROM Elenco_MP", conn)
        mp_lookup = dict(zip(mp_df['nome_mp'].str.lower(), mp_df['codice']))
        
        def find_codice(nome):
            if pd.isna(nome): return None
            n = str(nome).lower().strip()
            return mp_lookup.get(n)

        print("Collegamento materie prime e formattazione date...")
        df['codice_mp'] = df['materiale_nome'].apply(find_codice)
        
        df_to_save = df.drop(columns=['materiale_nome'])
        
        # Formattazione date YYYY-MM-DD
        date_cols = ['data_arrivo', 'data_scadenza', 'data_consegna_qc', 'data_approvazione', 'arrivo_magazzino']
        for col in date_cols:
            if col in df_to_save.columns:
                df_to_save[col] = pd.to_datetime(df_to_save[col], errors='coerce').dt.strftime('%Y-%m-%d')
                df_to_save[col] = df_to_save[col].fillna('')
        
        # Caricamento dati
        df_to_save.to_sql(table_name, conn, if_exists='append', index=False)
        conn.commit()
        
        print(f"Sincronizzazione completata! Caricati {len(df_to_save)} lotti.")
        conn.close()

    except Exception as e:
        print(f"Errore durante l'importazione: {e}")

if __name__ == "__main__":
    import_lotti()
