import sys
import os

# Aggiungi radice al path
sys.path.append(os.getcwd())

from app import app, get_db_connection
import sqlite3

def run_test():
    # 1. Prepariamo un lotto di test
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Rimuoviamo eventuali lotti di test vecchi
    cursor.execute("DELETE FROM Lotti_Interni WHERE lotto_interno = 'TEST_QC_001'")
    cursor.execute("DELETE FROM Elenco_MP WHERE codice = 'TEST_MP'")
    
    # Inseriamo materia prima di test
    cursor.execute("""
        INSERT INTO Elenco_MP (codice, nome_mp, nome_file, nome_etichetta, unita_misura, uso, controcampione, distribuzione)
        VALUES ('TEST_MP', 'Materia Prima Test QC', 'file.pdf', 'etich.pdf', 'Pz', 'Uso Test', 'NO', 'NO')
    """)
    
    # Inseriamo lotto di test
    cursor.execute("""
        INSERT INTO Lotti_Interni (lotto_interno, codice_mp, data_arrivo, data_scadenza, qnt_arrivata, fornitore, lotto_fornitore, giacenza, qc_attesa, data_consegna_qc)
        VALUES ('TEST_QC_001', 'TEST_MP', '2026-05-22', '2027-05-22', '10', 'Fornitore Test', 'LOT_FORN_123', '10', 'SI', NULL)
    """)
    
    conn.commit()
    conn.close()
    print("Database configurato con lotto di test.")
    
    # 2. Testiamo la rimozione dalla lista d'attesa (revert a grigio)
    client = app.test_client()
    print("Invocazione API /api/rimuovi_attesa_qc...")
    rem_resp = client.post('/api/rimuovi_attesa_qc/TEST_QC_001')
    print("Codice Risposta Rimozione:", rem_resp.status_code)
    
    conn = get_db_connection()
    row_rem = conn.execute("SELECT qc_attesa FROM Lotti_Interni WHERE lotto_interno = 'TEST_QC_001'").fetchone()
    print("Stato Database post-rimozione (attesa):", dict(row_rem)['qc_attesa'] if row_rem else "Lotto non trovato!")
    conn.close()
    
    # Ripristiniamo lo stato in attesa per completare il test di stampa
    conn = get_db_connection()
    conn.execute("UPDATE Lotti_Interni SET qc_attesa = 'SI' WHERE lotto_interno = 'TEST_QC_001'")
    conn.commit()
    conn.close()
    
    print("Invocazione API /api/stampa_richiesta_analisi...")
    response = client.post('/api/stampa_richiesta_analisi')
    print("Codice Risposta:", response.status_code)
    resp_data = response.get_json()
    print("Dati Risposta:", resp_data)
    
    # 3. Verifichiamo che il PDF sia stato creato
    expected_pdf = resp_data.get('filename') if resp_data else None
    expected_path = os.path.join("richiesta_analisi", expected_pdf) if expected_pdf else ""
    
    if os.path.exists(expected_path):
        print(f"Successo: Il PDF '{expected_path}' è stato creato correttamente!")
        # Stampiamo la dimensione del file
        print(f"Dimensione del file: {os.path.getsize(expected_path)} byte")
    else:
        print(f"Errore: Il PDF '{expected_path}' non è stato trovato!")
        
    # 4. Verifichiamo lo stato del database
    conn = get_db_connection()
    row = conn.execute("SELECT data_consegna_qc, qc_attesa FROM Lotti_Interni WHERE lotto_interno = 'TEST_QC_001'").fetchone()
    print("Stato Database post-stampa:", dict(row) if row else "Lotto non trovato!")
    
    # Pulizia database di test
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Lotti_Interni WHERE lotto_interno = 'TEST_QC_001'")
    cursor.execute("DELETE FROM Elenco_MP WHERE codice = 'TEST_MP'")
    conn.commit()
    conn.close()
    print("Pulizia database completata.")

if __name__ == '__main__':
    run_test()
