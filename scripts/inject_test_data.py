import sqlite3
import os

DB_PATH = os.path.join("database", "database.db")

def main():
    if not os.path.exists(DB_PATH):
        print(f"Errore: Database non trovato in {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Lotti mock da inserire
    mock_lotti = ['L-5612-EXP', 'L-5613-EXP', 'L-2073-SOON', 'L-5614-SOON']
    
    # Pulizia preliminare per rendere lo script idempotente
    print("Rimozione di eventuali lotti mock esistenti...")
    for lot in mock_lotti:
        cursor.execute("DELETE FROM Lotti_Interni WHERE lotto_interno = ?", (lot,))
    
    # Definizione lotti mock
    lotti_to_inject = [
        # LOTTI SCADUTI (rispetto alla data corrente: 2026-05-20)
        {
            'lotto_interno': 'L-5612-EXP',
            'data_arrivo': '2025-04-15',
            'codice_mp': '5612',          # Kit Hardware FET
            'lotto_fornitore': 'F-EXP-12',
            'fornitore': 'Fornitore Alfa',
            'data_scadenza': '2026-04-15', # Scaduto da circa un mese
            'qnt_arrivata': '5.0',
            'pz_x_cf': '1',
            'giacenza': '5.0',
            'appr': 'OK',
            'cc': 'NO',
            'chiuso': 'NO'
        },
        {
            'lotto_interno': 'L-5613-EXP',
            'data_arrivo': '2025-03-01',
            'codice_mp': '5613',          # QMA Eluent FET (2-8°C)
            'lotto_fornitore': 'F-EXP-13',
            'fornitore': 'Fornitore Beta',
            'data_scadenza': '2026-03-01', # Scaduto da più di due mesi
            'qnt_arrivata': '10.0',
            'pz_x_cf': '1',
            'giacenza': '10.0',
            'appr': 'OK',
            'cc': 'NO',
            'chiuso': 'NO'
        },
        # LOTTI IN SCADENZA IMMINENTE (< 30 giorni dal 2026-05-20)
        {
            'lotto_interno': 'L-2073-SOON',
            'data_arrivo': '2025-06-05',
            'codice_mp': '2073',          # Etanolo
            'lotto_fornitore': 'F-SOON-73',
            'fornitore': 'Fornitore Gamma',
            'data_scadenza': '2026-06-05', # Scadrà tra 16 giorni
            'qnt_arrivata': '20.0',
            'pz_x_cf': '1',
            'giacenza': '20.0',
            'appr': 'OK',
            'cc': 'NO',
            'chiuso': 'NO'
        },
        {
            'lotto_interno': 'L-5614-SOON',
            'data_arrivo': '2025-06-15',
            'codice_mp': '5614',          # Precursore FET
            'lotto_fornitore': 'F-SOON-14',
            'fornitore': 'Fornitore Delta',
            'data_scadenza': '2026-06-15', # Scadrà tra 26 giorni
            'qnt_arrivata': '15.0',
            'pz_x_cf': '1',
            'giacenza': '15.0',
            'appr': 'OK',
            'cc': 'NO',
            'chiuso': 'NO'
        }
    ]

    print("Inserimento dei lotti mock...")
    for data in lotti_to_inject:
        cursor.execute('''
            INSERT INTO Lotti_Interni 
            (lotto_interno, data_arrivo, codice_mp, lotto_fornitore, fornitore, data_scadenza, 
             qnt_arrivata, pz_x_cf, giacenza, appr, cc, chiuso) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['lotto_interno'], data['data_arrivo'], data['codice_mp'], data['lotto_fornitore'],
            data['fornitore'], data['data_scadenza'], data['qnt_arrivata'], data['pz_x_cf'],
            data['giacenza'], data['appr'], data['cc'], data['chiuso']
        ))
    
    conn.commit()
    conn.close()
    print("Iniezione completata con successo!")

if __name__ == '__main__':
    main()
