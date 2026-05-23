import sqlite3
import json
from datetime import datetime
from config import RESOLVED_DB_PATH

def get_db_connection():
    conn = sqlite3.connect(RESOLVED_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_audit_db():
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Audit_Trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_ora TEXT NOT NULL,
                operatore TEXT,
                azione TEXT NOT NULL,
                tabella_interessata TEXT NOT NULL,
                vecchio_valore TEXT,
                nuovo_valore TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        print(f"Errore durante la creazione della tabella Audit_Trail: {e}")
    finally:
        conn.close()

def init_etichette_db():
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Storico_Etichette (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_ora TEXT NOT NULL,
                lotto_interno TEXT NOT NULL,
                codice_mp TEXT NOT NULL,
                nome_mp TEXT NOT NULL,
                data_arrivo TEXT NOT NULL,
                quantita TEXT NOT NULL,
                tipo_stampa TEXT NOT NULL,
                operatore TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        print(f"Errore durante la creazione della tabella Storico_Etichette: {e}")
    finally:
        conn.close()

def log_audit(azione, tabella_interessata, operatore, vecchio_valore=None, nuovo_valore=None, conn=None):
    data_ora = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    
    vecchio_val_str = json.dumps(vecchio_valore) if isinstance(vecchio_valore, (dict, list)) else vecchio_valore
    nuovo_val_str = json.dumps(nuovo_valore) if isinstance(nuovo_valore, (dict, list)) else nuovo_valore
    
    if not operatore or not str(operatore).strip():
        operatore = "Sistema"
        
    local_conn = False
    if conn is None:
        conn = get_db_connection()
        local_conn = True
        
    try:
        conn.execute('''
            INSERT INTO Audit_Trail (data_ora, operatore, azione, tabella_interessata, vecchio_valore, nuovo_valore)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data_ora, operatore, azione, tabella_interessata, vecchio_val_str, nuovo_val_str))
        if local_conn:
            conn.commit()
    except Exception as e:
        print(f"Errore durante l'inserimento dell'audit trail: {e}")
    finally:
        if local_conn:
            conn.close()
