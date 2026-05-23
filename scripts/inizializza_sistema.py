import os
import sys
import sqlite3
import random
import argparse
from datetime import datetime, date, timedelta

# Aggiungi il root del progetto al sys.path per importare config e db_utils correttamente
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import (
    RESOLVED_DB_PATH,
    RESOLVED_LISTA_DISTRIBUZIONE_DIR,
    RESOLVED_RICHIESTA_ANALISI_DIR,
    RESOLVED_PICKING_LIST_DIR
)
from db_utils import log_audit

def empty_folder(folder_path):
    """Elimina tutti i file all'interno della cartella specificata mantenendo la struttura."""
    if not os.path.exists(folder_path):
        print(f"La cartella {folder_path} non esiste. Creazione...")
        os.makedirs(folder_path, exist_ok=True)
        return
        
    print(f"Svuotamento cartella: {folder_path}...")
    count = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Non eliminare i file di configurazione nascosti
            if file.startswith('.'):
                continue
            file_path = os.path.join(root, file)
            try:
                os.remove(file_path)
                count += 1
            except Exception as e:
                print(f"Errore durante l'eliminazione di {file_path}: {e}")
    print(f"Rimossi {count} file da {folder_path}.")

def clear_database():
    """Svuota tutte le tabelle utente del database SQLite e resetta i contatori auto-increment."""
    print(f"Connessione al database: {RESOLVED_DB_PATH}...")
    if not os.path.exists(RESOLVED_DB_PATH):
        print(f"Avviso: Il database {RESOLVED_DB_PATH} non esiste. Verrà creato.")
        
    conn = sqlite3.connect(RESOLVED_DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Disabilita i vincoli delle foreign key per lo svuotamento
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # Recupera tutte le tabelle utente
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Tabelle trovate nel database da svuotare: {tables}")
        for table in tables:
            print(f"Svuotamento tabella: {table}...")
            cursor.execute(f"DELETE FROM {table};")
            
        # Resetta i contatori auto-increment se esiste sqlite_sequence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence';")
        if cursor.fetchone():
            print("Reset dei contatori auto-increment in sqlite_sequence...")
            cursor.execute("DELETE FROM sqlite_sequence;")
            
        conn.commit()
        print("Database svuotato correttamente!")
    except Exception as e:
        print(f"Errore durante lo svuotamento del database: {e}")
        conn.rollback()
        raise e
    finally:
        # Riabilita le foreign key ed esegue l'ottimizzazione VACUUM
        cursor.execute("PRAGMA foreign_keys = ON;")
        print("Ottimizzazione database (VACUUM)...")
        cursor.execute("VACUUM;")
        conn.close()

def populate_fornitori():
    """Popola la tabella Fornitori con dati mock di prova."""
    conn = sqlite3.connect(RESOLVED_DB_PATH)
    cursor = conn.cursor()
    try:
        print("Inserimento fornitori di prova...")
        fornitori = [("Fornitore Alfa",), ("Fornitore Beta",)]
        cursor.executemany("INSERT INTO Fornitori (nome) VALUES (?)", fornitori)
        conn.commit()
        print("Fornitori caricati con successo.")
    except Exception as e:
        print(f"Errore nell'inserimento dei fornitori: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def populate_materials():
    """Popola la tabella Elenco_MP con i 15 ingredienti dello scarico 'Picking FDG (Synthera)'."""
    conn = sqlite3.connect(RESOLVED_DB_PATH)
    cursor = conn.cursor()
    try:
        print("Popolamento materie prime per lo scarico 'Picking FDG (Synthera)'...")
        materie_base = [
            ("741", "Kit IFP Synthera", "Kit IFP Synthera", "pz", "Kit IFP Synthera", "FDG", "", "NO", "NO", 999, "Kit"),
            ("2065", "Kit chimico reagenti Synthera", "Kit chimico reagenti Synthera", "pz", "Kit chimico reagenti Synthera", "FDG", "", "NO", "NO", 999, "Kit"),
            ("742", "Mannosio Triflato Synthera", "Mannosio Triflato Synthera", "pz", "Mannosio Triflato Synthera", "FDG", "", "NO", "NO", 999, "Kit"),
            ("740", "Kit accessori Synthera", "Kit accessori Synthera", "pz", "Kit accessori Synthera", "FDG", "", "NO", "NO", 999, "Kit"),
            ("461", "Kit di frazionamento", "Kit di frazionamento", "pz", "Kit di frazionamento", "FDG", "", "NO", "NO", 999, "Kit"),
            ("1368", "Filtro Millex OR 0.22 micron", "Filtro Millex OR 0.22 micron", "pz", "Filtro Millex OR 0.22 micron", "FDG", "", "NO", "NO", 999, "Filtri"),
            ("701", "Sodio cloruro 0,9% (250 ml)", "Sodio cloruro 0,9% (250 ml)", "pz", "Sodio cloruro 0,9% (250 ml)", "FDG", "", "NO", "NO", 999, "Reagenti"),
            ("4379", "Flaconi sterili apirogeni crimpati HUAYI", "Flaconi sterili apirogeni crimpati HUAYI", "pz", "Flaconi sterili apirogeni crimpati HUAYI", "FDG", "", "NO", "NO", 999, "Consumabili"),
            ("4380", "Capsule sterili HUAYI", "Capsule sterili HUAYI", "pz", "Capsule sterili HUAYI", "FDG", "", "NO", "NO", 999, "Consumabili"),
            ("605", "Piastre TSA 55 mm", "Piastre TSA 55 mm", "pz", "Piastre TSA 55 mm", "FDG", "", "NO", "NO", 999, "Consumabili"),
            ("606", "Piastre TSA 90 mm", "Piastre TSA 90 mm", "pz", "Piastre TSA 90 mm", "FDG", "", "NO", "NO", 999, "Consumabili"),
            ("521", "Sodio Cloruro 10%", "Sodio Cloruro 10%", "pz", "Sodio Cloruro 10%", "FDG", "", "NO", "NO", 999, "Reagenti"),
            ("3600", "Kit aggiuntivo di frazionamento", "Kit aggiuntivo di frazionamento", "pz", "Kit aggiuntivo di frazionamento", "FDG", "", "NO", "NO", 999, "Kit"),
            ("4357", "Etanolo eccipiente", "Etanolo eccipiente", "pz", "Etanolo eccipiente", "FDG", "", "NO", "NO", 999, "Reagenti"),
            ("424", "Acqua arricchita [18O]H2O", "Acqua arricchita [18O]H2O", "g", "Acqua arricchita [18O]H2O", "FDG", "", "NO", "NO", 999, "Reagenti")
        ]
        
        materie_finali = []
        for item in materie_base:
            codice, nome_mp, nome_file, unita_misura, nome_etichetta, uso, codice_fornitore, controcampione, distribuzione, ordine_magazzino, categoria_magazzino = item
            
            # Genera scorta_minima casuale
            if unita_misura == 'g':
                scorta_min = round(random.uniform(1.0, 5.0), 1)
            else:
                scorta_min = float(random.randint(2, 8))
                
            materie_finali.append((
                codice, nome_mp, nome_file, unita_misura, nome_etichetta, uso, 
                codice_fornitore, controcampione, distribuzione, scorta_min, 
                ordine_magazzino, categoria_magazzino
            ))
            
        cursor.executemany("""
            INSERT INTO Elenco_MP 
            (codice, nome_mp, nome_file, unita_misura, nome_etichetta, uso, codice_fornitore, controcampione, distribuzione, scorta_minima, ordine_magazzino, categoria_magazzino)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, materie_finali)
        conn.commit()
        print(f"Inserite con successo {len(materie_finali)} materie prime con scorte minime casuali.")
        return materie_finali
    except Exception as e:
        print(f"Errore nel popolamento delle materie prime: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def populate_lots(materials):
    """Popola la tabella Lotti_Interni con 2 lotti per materia prima, inseriti come da pagina 'Nuovo Lotto'."""
    conn = sqlite3.connect(RESOLVED_DB_PATH)
    cursor = conn.cursor()
    
    today = date.today()
    expired_count = 0
    
    try:
        print("Registrazione di due lotti interni per ciascuna materia prima...")
        for i, mat in enumerate(materials):
            codice_mp = mat[0]
            nome_mp = mat[1]
            unita = mat[3]
            
            # Lotto 1: scaduto (esattamente 2 in tutto il sistema) o in scadenza ma valido
            if expired_count < 2:
                # Scaduto
                days_ago = random.randint(15, 30)
                data_scadenza = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                expired_count += 1
            else:
                # In scadenza ma ancora valido (futuro prossimo)
                days_ahead = random.randint(5, 15)
                data_scadenza = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
                
            data_arrivo_1 = (today - timedelta(days=random.randint(10, 20))).strftime('%Y-%m-%d')
            fornitore_1 = "Fornitore Alfa" if i % 2 == 0 else "Fornitore Beta"
            qnt_1 = "500.0" if unita == 'g' else "100"
            lotto_int_1 = f"LI-{codice_mp}-01"
            
            # Lotto 2: abbondantemente lontano nel futuro
            data_scadenza_2 = (today + timedelta(days=random.randint(400, 600))).strftime('%Y-%m-%d')
            data_arrivo_2 = (today - timedelta(days=random.randint(1, 4))).strftime('%Y-%m-%d')
            fornitore_2 = "Fornitore Beta" if i % 2 == 0 else "Fornitore Alfa"
            qnt_2 = "1000.0" if unita == 'g' else "200"
            lotto_int_2 = f"LI-{codice_mp}-02"
            
            lotti_data = [
                {
                    'lotto_interno': lotto_int_1,
                    'codice_mp': codice_mp,
                    'data_arrivo': data_arrivo_1,
                    'lotto_fornitore': f"LOT-FORN-{codice_mp}-A",
                    'fornitore': fornitore_1,
                    'data_scadenza': data_scadenza,
                    'qnt_arrivata': qnt_1,
                    'pz_x_cf': "1",
                    'giacenza': qnt_1,
                    'in_uso': "SI"
                },
                {
                    'lotto_interno': lotto_int_2,
                    'codice_mp': codice_mp,
                    'data_arrivo': data_arrivo_2,
                    'lotto_fornitore': f"LOT-FORN-{codice_mp}-B",
                    'fornitore': fornitore_2,
                    'data_scadenza': data_scadenza_2,
                    'qnt_arrivata': qnt_2,
                    'pz_x_cf': "1",
                    'giacenza': qnt_2,
                    'in_uso': "SI"
                }
            ]
            
            for lot in lotti_data:
                # Inserimento nel database
                cursor.execute('''
                    INSERT INTO Lotti_Interni 
                    (lotto_interno, codice_mp, data_arrivo, lotto_fornitore, fornitore, data_scadenza, 
                     qnt_arrivata, pz_x_cf, giacenza, in_uso) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lot['lotto_interno'], lot['codice_mp'], lot['data_arrivo'], 
                    lot['lotto_fornitore'], lot['fornitore'], lot['data_scadenza'],
                    lot['qnt_arrivata'], lot['pz_x_cf'], lot['giacenza'], lot['in_uso']
                ))
                
                # Log audit trail (replica l'inserimento standard dell'applicazione)
                lot_audit_data = lot.copy()
                lot_audit_data['mp_search'] = f"{codice_mp} - {nome_mp}"
                log_audit(
                    azione="INSERIMENTO",
                    tabella_interessata="Lotti_Interni",
                    operatore="Sistema",
                    nuovo_valore=lot_audit_data,
                    conn=conn
                )
                
        conn.commit()
        print("Tutti i lotti sono stati registrati con successo con relativo log nell'Audit Trail.")
    except Exception as e:
        print(f"Errore durante l'inserimento dei lotti: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Inizializza il sistema ripristinando il database e le cartelle PDF.")
    parser.add_argument('--force', action='store_true', help="Salta la richiesta di conferma interattiva.")
    args = parser.parse_args()
    
    if not args.force:
        print("\n=== ATTENZIONE ===")
        print("Questo script eseguirà le seguenti operazioni distruttive:")
        print(f"1. Eliminerà TUTTI i file nelle cartelle:")
        print(f"   - {RESOLVED_LISTA_DISTRIBUZIONE_DIR}")
        print(f"   - {RESOLVED_RICHIESTA_ANALISI_DIR}")
        print(f"   - {RESOLVED_PICKING_LIST_DIR}")
        print(f"2. SVUOTERÀ completamente il database a: {RESOLVED_DB_PATH}")
        print("Poi ripopolerà il database con i dati iniziali di prova (materie prime FDG e lotti mock).\n")
        
        confirm = input("Sei SICURO di voler procedere? (s/n): ")
        if confirm.lower() != 's':
            print("Operazione annullata.")
            sys.exit(0)
            
    print("\n--- INIZIO RESET DI SISTEMA ---")
    
    # 1. Svuotamento cartelle PDF
    empty_folder(RESOLVED_LISTA_DISTRIBUZIONE_DIR)
    empty_folder(RESOLVED_RICHIESTA_ANALISI_DIR)
    empty_folder(RESOLVED_PICKING_LIST_DIR)
    
    # 2. Svuotamento database
    clear_database()
    
    # 3. Ripopolamento
    populate_fornitori()
    materials = populate_materials()
    populate_lots(materials)
    
    print("\n--- RESET E INIZIALIZZAZIONE DI SISTEMA COMPLETATI CON SUCCESSO! ---")

if __name__ == '__main__':
    main()
