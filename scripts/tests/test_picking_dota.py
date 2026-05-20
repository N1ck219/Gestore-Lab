import sqlite3
import os

# Determinazione del path corretto del database
if os.path.exists(os.path.join("database", "database.db")):
    DB_PATH = os.path.join("database", "database.db")
elif os.path.exists(os.path.join("..", "..", "database", "database.db")):
    DB_PATH = os.path.join("..", "..", "database", "database.db")
else:
    DB_PATH = os.path.join("database", "database.db")

def run_test():
    print("--- [TEST START: Picking DOTA] ---")
    
    # 1. Connessione
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 2. Svuotamento Tabelle
    print("Svuotamento tabelle esistenti...")
    cursor.execute("PRAGMA foreign_keys = OFF;")
    cursor.execute("DELETE FROM Scarichi;")
    cursor.execute("DELETE FROM Lotti_Interni;")
    cursor.execute("DELETE FROM Elenco_MP;")
    cursor.execute("DELETE FROM Fornitori;")
    cursor.execute("DELETE FROM sqlite_sequence;")
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 3. Inserimento Fornitori Mock
    print("Inserimento fornitori di prova...")
    fornitori = [("Fornitore Alfa",), ("Fornitore Beta",)]
    cursor.executemany("INSERT INTO Fornitori (nome) VALUES (?)", fornitori)
    
    # 4. Inserimento Materie Prime
    print("Inserimento materie prime coinvolte nel picking...")
    materie = [
        ("4482", "DOPA Trasis Cassette", "DOPA Trasis Cassette", "pz", "DOPA Trasis Cassette", "DOTA", "", "NO", "NO", 0.0, 999, "Kit"),
        ("4483", "DOPA Trasis Kit 1 (2-8°C)", "DOPA Trasis Kit 1 (2-8°C)", "pz", "DOPA Trasis Kit 1 (2-8°C)", "DOTA", "", "NO", "NO", 0.0, 999, "Kit"),
        ("4484", "DOPA Trasis Kit 2", "DOPA Trasis Kit 2", "pz", "DOPA Trasis Kit 2", "DOTA", "", "NO", "NO", 0.0, 999, "Kit"),
        ("4486", "Acqua PPI Bottiglia 1L", "Acqua PPI Bottiglia 1L", "pz", "Acqua PPI Bottiglia 1L", "DOTA", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("4523", "Acqua PPI Bottiglia 250ml", "Acqua PPI Bottiglia 250ml", "pz", "Acqua PPI Bottiglia 250ml", "DOTA", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("4487", "Acqua PPI Bag 250ml", "Acqua PPI Bag 250ml", "pz", "Acqua PPI Bag 250ml", "DOTA", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("2073", "Etanolo", "Etanolo", "ml", "Etanolo", "DOTA", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("4485", "Acido ascorbico", "Acido ascorbico", "g", "Acido ascorbico", "DOTA", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("3945", "Acido acetico", "Acido acetico", "ml", "Acido acetico", "DOTA", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("4491", "Sodio acetato triidrato", "Sodio acetato triidrato", "g", "Sodio acetato triidrato", "DOTA", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("461", "Kit di frazionamento", "Kit di frazionamento", "pz", "Kit di frazionamento", "DOTA", "", "NO", "NO", 0.0, 999, "Kit"),
        ("4622", "Vials 100ml sterile", "Vials 100ml sterile", "pz", "Vials 100ml sterile", "DOTA", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("2074", "Filtro Millex GS Vented", "Filtro Millex GS Vented", "pz", "Filtro Millex GS Vented", "DOTA", "", "NO", "NO", 0.0, 999, "Filtri"),
        ("1368", "Filtro Millex OR 0.22 micron", "Filtro Millex OR 0.22 micron", "pz", "Filtro Millex OR 0.22 micron", "DOTA", "", "NO", "NO", 0.0, 999, "Filtri"),
        ("4379", "Flaconi sterili apirogeni crimpati HUAYI", "Flaconi sterili apirogeni crimpati HUAYI", "pz", "Flaconi sterili apirogeni crimpati HUAYI", "DOTA", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("4380", "Capsule sterili HUAYI", "Capsule sterili HUAYI", "pz", "Capsule sterili HUAYI", "DOTA", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("605", "Piastre TSA 55 mm", "Piastre TSA 55 mm", "pz", "Piastre TSA 55 mm", "DOTA", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("606", "Piastre TSA 90 mm", "Piastre TSA 90 mm", "pz", "Piastre TSA 90 mm", "DOTA", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("424", "Acqua arricchita [18O]H2O", "Acqua arricchita [18O]H2O", "g", "Acqua arricchita [18O]H2O", "DOTA", "", "NO", "NO", 0.0, 999, "Reagenti")
    ]
    cursor.executemany("""
        INSERT INTO Elenco_MP 
        (codice, nome_mp, nome_file, unita_misura, nome_etichetta, uso, codice_fornitore, controcampione, distribuzione, scorta_minima, ordine_magazzino, categoria_magazzino)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, materie)
    
    # 5. Inserimento Lotti (due per ogni materia prima con date differenti)
    print("Registrazione di due lotti per ciascuna materia prima...")
    lotti = []
    for item in materie:
        codice = item[0]
        # Lotto 1
        lotti.append((
            f"L-{codice}-01", # lotto_interno
            "2026-05-01",     # data_arrivo
            codice,           # codice_mp
            f"F-{codice}-A",  # lotto_fornitore
            "Fornitore Alfa", # fornitore
            "2027-05-01",     # data_scadenza
            "100.0",          # qnt_arrivata
            "1",              # pz_x_cf
            "100.0",          # giacenza
            "2026-05-01",     # data_consegna_qc
            "2026-05-02",     # data_approvazione
            "2026-05-02",     # arrivo_magazzino
            "0",              # consumi
            "",               # ca
            "CAMERA CALDA",   # reparto
            "OK",             # appr
            "OK",             # etich
            "OK",             # cc
            f"CL-{codice}-1", # codice_lotto
            "SI",             # in_uso
            "NO"              # chiuso
        ))
        # Lotto 2 (data differente)
        lotti.append((
            f"L-{codice}-02", # lotto_interno
            "2026-05-10",     # data_arrivo
            codice,           # codice_mp
            f"F-{codice}-B",  # lotto_fornitore
            "Fornitore Beta", # fornitore
            "2027-05-10",     # data_scadenza
            "100.0",          # qnt_arrivata
            "1",              # pz_x_cf
            "100.0",          # giacenza
            "2026-05-10",     # data_consegna_qc
            "2026-05-11",     # data_approvazione
            "2026-05-11",     # arrivo_magazzino
            "0",              # consumi
            "",               # ca
            "CAMERA CALDA",   # reparto
            "OK",             # appr
            "OK",             # etich
            "OK",             # cc
            f"CL-{codice}-2", # codice_lotto
            "SI",             # in_uso
            "NO"              # chiuso
        ))
        
    cursor.executemany("""
        INSERT INTO Lotti_Interni 
        (lotto_interno, data_arrivo, codice_mp, lotto_fornitore, fornitore, data_scadenza, qnt_arrivata, pz_x_cf, giacenza, data_consegna_qc, data_approvazione, arrivo_magazzino, consumi, ca, reparto, appr, etich, cc, codice_lotto, in_uso, chiuso)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, lotti)
    
    conn.commit()
    
    # 6. Verifica
    res_mp = cursor.execute("SELECT COUNT(*) FROM Elenco_MP").fetchone()[0]
    res_lotti = cursor.execute("SELECT COUNT(*) FROM Lotti_Interni").fetchone()[0]
    
    print(f"Verifica completata: {res_mp} materie prime inserite, {res_lotti} lotti registrati.")
    print("--- [TEST SUCCESSO: Picking DOTA] ---")
    conn.close()

if __name__ == '__main__':
    run_test()
