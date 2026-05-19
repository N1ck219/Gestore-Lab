import sqlite3
import os

DB_PATH = os.path.join("database", "database.db")

def insert_missing_products():
    new_products = [
        {
            'codice': '4599',
            'nome_mp': 'Kit Hardware FDG TRASIS',
            'nome_file': 'Kit Hardware FDG TRASIS',
            'unita_misura': 'pz',
            'nome_etichetta': 'Kit Hardware FDG TRASIS',
            'uso': 'FDG',
            'codice_fornitore': '',
            'controcampione': 'NO',
            'distribuzione': 'NO',
            'scorta_minima': 0.0,
            'ordine_magazzino': 999
        },
        {
            'codice': '4600',
            'nome_mp': 'Kit reagenti FDG TRASIS',
            'nome_file': 'Kit reagenti FDG TRASIS',
            'unita_misura': 'pz',
            'nome_etichetta': 'Kit reagenti FDG TRASIS',
            'uso': 'FDG',
            'codice_fornitore': '',
            'controcampione': 'NO',
            'distribuzione': 'NO',
            'scorta_minima': 0.0,
            'ordine_magazzino': 999
        },
        {
            'codice': '4601',
            'nome_mp': 'Mannosio Triflato TRASIS',
            'nome_file': 'Mannosio Triflato TRASIS',
            'unita_misura': 'pz',
            'nome_etichetta': 'Mannosio Triflato TRASIS',
            'uso': 'FDG',
            'codice_fornitore': '',
            'controcampione': 'NO',
            'distribuzione': 'NO',
            'scorta_minima': 0.0,
            'ordine_magazzino': 999
        },
        {
            'codice': '5694',
            'nome_mp': 'Chromabond FDG TRASIS',
            'nome_file': 'Chromabond FDG TRASIS',
            'unita_misura': 'pz',
            'nome_etichetta': 'Chromabond FDG TRASIS',
            'uso': 'FDG',
            'codice_fornitore': '',
            'controcampione': 'NO',
            'distribuzione': 'NO',
            'scorta_minima': 0.0,
            'ordine_magazzino': 999
        },
        {
            'codice': '4602',
            'nome_mp': 'Acqua PPI Bag 1L',
            'nome_file': 'Acqua PPI Bag 1L',
            'unita_misura': 'pz',
            'nome_etichetta': 'Acqua PPI Bag 1L',
            'uso': 'FDG',
            'codice_fornitore': '',
            'controcampione': 'NO',
            'distribuzione': 'NO',
            'scorta_minima': 0.0,
            'ordine_magazzino': 999
        },
        {
            'codice': '2074',
            'nome_mp': 'Filtro Millex GS Vented',
            'nome_file': 'Filtro Millex GS Vented',
            'unita_misura': 'pz',
            'nome_etichetta': 'Filtro Millex GS Vented',
            'uso': 'FDG',
            'codice_fornitore': '',
            'controcampione': 'NO',
            'distribuzione': 'NO',
            'scorta_minima': 0.0,
            'ordine_magazzino': 999
        }
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    inserted_count = 0
    for p in new_products:
        # Check if product with this code already exists
        cursor.execute("SELECT COUNT(*) FROM Elenco_MP WHERE codice = ?", (p['codice'],))
        exists = cursor.fetchone()[0] > 0
        if not exists:
            cursor.execute("""
                INSERT INTO Elenco_MP (codice, nome_mp, nome_file, unita_misura, nome_etichetta, uso, codice_fornitore, controcampione, distribuzione, scorta_minima, ordine_magazzino)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (p['codice'], p['nome_mp'], p['nome_file'], p['unita_misura'], p['nome_etichetta'], p['uso'], p['codice_fornitore'], p['controcampione'], p['distribuzione'], p['scorta_minima'], p['ordine_magazzino']))
            inserted_count += 1
            print(f"Inserted: {p['nome_mp']} ({p['codice']})")
        else:
            print(f"Already exists: {p['nome_mp']} ({p['codice']})")
            
    conn.commit()
    conn.close()
    print(f"Done! Inserted {inserted_count} new products.")

if __name__ == '__main__':
    insert_missing_products()
