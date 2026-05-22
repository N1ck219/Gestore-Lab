import sys
import os

# Aggiungi il percorso principale se necessario
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

def test_app_routes():
    print("Inizializzazione Flask test client...")
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        # Test della homepage
        print("Test della homepage (/) ...")
        res_home = client.get('/')
        print(f"Risultato homepage: {res_home.status_code}")
        assert res_home.status_code == 200, f"Errore caricamento homepage: {res_home.status_code}"
        
        # Test di Nuova Etichetta
        print("Test della pagina Nuova Etichetta (/nuova_etichetta) ...")
        res_nuova = client.get('/nuova_etichetta')
        print(f"Risultato nuova etichetta: {res_nuova.status_code}")
        assert res_nuova.status_code == 200, f"Errore caricamento nuova etichetta: {res_nuova.status_code}"
        
        # Test di Storico Etichetta
        print("Test della pagina Storico Etichetta (/storico_etichetta) ...")
        res_storico = client.get('/storico_etichetta')
        print(f"Risultato storico etichetta: {res_storico.status_code}")
        # Test delle rotte dei Log di Sistema
        print("Test del recupero log (/settings/logs) ...")
        res_logs = client.get('/settings/logs')
        print(f"Risultato log JSON: {res_logs.status_code}")
        assert res_logs.status_code == 200, f"Errore caricamento log: {res_logs.status_code}"
        assert res_logs.get_json()['success'] is True, f"Risposta log non valida: {res_logs.get_json()}"

        print("Test di download log (/settings/logs/download) ...")
        res_log_dl = client.get('/settings/logs/download')
        print(f"Risultato download log: {res_log_dl.status_code}")
        assert res_log_dl.status_code == 200, f"Errore download log: {res_log_dl.status_code}"

        # Test di salvataggio etichetta tramite API
        import time
        unique_lot = f"TEST_LOT_{int(time.time())}"
        print(f"Test dell'API di salvataggio etichetta (/api/salva_etichetta) con {unique_lot} ...")
        res_salva = client.post('/api/salva_etichetta', json={
            'lotto_interno': unique_lot,
            'nome_mp': 'Test Materia Prima',
            'codice_mp': 'TEST_CODE_01',
            'data_arrivo': '22-05-2026',
            'quantita': '100 Kg',
            'tipo_stampa': 'GIALLO'
        })
        print(f"Risultato API salvataggio: {res_salva.status_code}, data: {res_salva.get_json()}")
        assert res_salva.status_code == 200, f"Errore chiamata API salva_etichetta: {res_salva.status_code}"
        assert res_salva.get_json()['success'] is True, f"Risposta API non valida: {res_salva.get_json()}"
        
        # Test dei vincoli per la stampa dell'etichetta VERDE
        print("\nTest dei vincoli per l'Etichetta VERDE...")
        
        # 1. Deve fallire se la bianca non è stata ancora generata
        res_verde_no_white = client.post('/api/salva_etichetta', json={
            'lotto_interno': 'TEST_LOT_VERDE_NO_WHITE',
            'nome_mp': 'Test Materia Prima',
            'codice_mp': 'TEST_CODE_01',
            'data_arrivo': '22-05-2026',
            'quantita': '100 Kg',
            'tipo_stampa': 'VERDE'
        })
        print(f"Stampa verde senza bianca: status_code={res_verde_no_white.status_code}, data={res_verde_no_white.get_json()}")
        assert res_verde_no_white.status_code == 400
        assert "etichetta bianca non è stata ancora generata" in res_verde_no_white.get_json()['message']
        
        # Aggiungiamo prima un lotto reale nel DB per testare gli altri vincoli (qc e appr)
        import sqlite3
        conn = sqlite3.connect(os.path.join("database", "database.db"))
        
        # Creiamo un lotto di test
        test_lotto_id = f"TEST_LOT_CONSTRAINTS_{int(time.time())}"
        conn.execute('''
            INSERT INTO Lotti_Interni (lotto_interno, codice_mp, data_arrivo, qnt_arrivata, data_consegna_qc, appr, chiuso)
            VALUES (?, 'TEST_CODE_01', '2026-05-22', '100', '-', '-', 'NO')
        ''', (test_lotto_id,))
        conn.commit()
        
        # 2. Generiamo prima l'etichetta BIANCO per questo lotto
        res_white = client.post('/api/salva_etichetta', json={
            'lotto_interno': test_lotto_id,
            'nome_mp': 'Test Materia Prima',
            'codice_mp': 'TEST_CODE_01',
            'data_arrivo': '22-05-2026',
            'quantita': '100 Kg',
            'tipo_stampa': 'BIANCO'
        })
        assert res_white.status_code == 200
        
        # Ora proviamo a stampare VERDE. Deve fallire perché QC e Appr non sono impostati.
        res_verde_no_qc = client.post('/api/salva_etichetta', json={
            'lotto_interno': test_lotto_id,
            'nome_mp': 'Test Materia Prima',
            'codice_mp': 'TEST_CODE_01',
            'data_arrivo': '22-05-2026',
            'quantita': '100 Kg',
            'tipo_stampa': 'VERDE'
        })
        print(f"Stampa verde senza QC: status_code={res_verde_no_qc.status_code}, data={res_verde_no_qc.get_json()}")
        assert res_verde_no_qc.status_code == 400
        assert "QC non è ancora stato impostato" in res_verde_no_qc.get_json()['message']
        
        # Impostiamo il QC consegnato ma Appr a '-'
        conn.execute('''
            UPDATE Lotti_Interni
            SET data_consegna_qc = '2026-05-22', appr = '-'
            WHERE lotto_interno = ?
        ''', (test_lotto_id,))
        conn.commit()
        
        # Ora proviamo a stampare VERDE. Deve fallire perché Appr non è 'OK'.
        res_verde_no_ok = client.post('/api/salva_etichetta', json={
            'lotto_interno': test_lotto_id,
            'nome_mp': 'Test Materia Prima',
            'codice_mp': 'TEST_CODE_01',
            'data_arrivo': '22-05-2026',
            'quantita': '100 Kg',
            'tipo_stampa': 'VERDE'
        })
        print(f"Stampa verde senza Appr OK: status_code={res_verde_no_ok.status_code}, data={res_verde_no_ok.get_json()}")
        assert res_verde_no_ok.status_code == 400
        assert "non è stato ancora approvato" in res_verde_no_ok.get_json()['message']
        
        # Impostiamo Appr a 'OK'
        conn.execute('''
            UPDATE Lotti_Interni
            SET appr = 'OK'
            WHERE lotto_interno = ?
        ''', (test_lotto_id,))
        conn.commit()
        
        # Ora deve riuscire con successo!
        res_verde_success = client.post('/api/salva_etichetta', json={
            'lotto_interno': test_lotto_id,
            'nome_mp': 'Test Materia Prima',
            'codice_mp': 'TEST_CODE_01',
            'data_arrivo': '22-05-2026',
            'quantita': '100 Kg',
            'tipo_stampa': 'VERDE'
        })
        print(f"Stampa verde con tutti i requisiti soddisfatti: status_code={res_verde_success.status_code}, data={res_verde_success.get_json()}")
        assert res_verde_success.status_code == 200
        assert res_verde_success.get_json()['success'] is True
        
        # Puliamo il lotto di test dal database per non lasciare spazzatura
        conn.execute("DELETE FROM Lotti_Interni WHERE lotto_interno = ?", (test_lotto_id,))
        conn.execute("DELETE FROM Storico_Etichette WHERE lotto_interno = ?", (test_lotto_id,))
        conn.commit()
        conn.close()
        
        print("\nTutti i test sulle nuove pagine, l'API e la homepage sono passati con successo (HTTP 200 OK)!")

if __name__ == '__main__':
    try:
        test_app_routes()
    except AssertionError as e:
        print(f"\n[ERRORE DI COERENZA]: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRORE GENERALE]: {e}")
        sys.exit(1)
