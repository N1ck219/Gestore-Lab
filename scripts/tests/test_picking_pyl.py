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
    print("--- [TEST START: Picking PYL] ---")
    
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
        ("5365", "Kit hardware PYL", "Kit hardware PYL", "pz", "Kit hardware PYL", "PYL", "", "NO", "NO", 0.0, 999, "Kit"),
        ("5366", "Kit regenti PYL", "Kit regenti PYL", "pz", "Kit regenti PYL", "PYL", "", "NO", "NO", 0.0, 999, "Kit"),
        ("5368", "Precursore PYL", "Precursore PYL", "pz", "Precursore PYL", "PYL", "", "NO", "NO", 0.0, 999, "Kit"),
        ("5367", "QMA Eluent PYL", "QMA Eluent PYL", "pz", "QMA Eluent PYL", "PYL", "", "NO", "NO", 0.0, 999, "Kit"),
        ("5585", "Acetonitrile HPLC", "Acetonitrile HPLC", "ml", "Acetonitrile HPLC", "PYL", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("2073", "Etanolo", "Etanolo", "ml", "Etanolo", "PYL", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("4487", "Acqua PPI Bag 250ml", "Acqua PPI Bag 250ml", "pz", "Acqua PPI Bag 250ml", "PYL", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("63", "Acqua PPI 500ml", "Acqua PPI 500ml", "pz", "Acqua PPI 500ml", "PYL", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("5584", "Filtro Pall", "Filtro Pall", "pz", "Filtro Pall", "PYL", "", "NO", "NO", 0.0, 999, "Filtri"),
        ("1368", "Filtro Millex OR 0.22 micron", "Filtro Millex OR 0.22 micron", "pz", "Filtro Millex OR 0.22 micron", "PYL", "", "NO", "NO", 0.0, 999, "Filtri"),
        ("461", "Kit di frazionamento", "Kit di frazionamento", "pz", "Kit di frazionamento", "PYL", "", "NO", "NO", 0.0, 999, "Kit"),
        ("701", "Sodio cloruro 0,9% (250 ml)", "Sodio cloruro 0,9% (250 ml)", "pz", "Sodio cloruro 0,9% (250 ml)", "PYL", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("4379", "Flaconi sterili apirogeni crimpati HUAYI", "Flaconi sterili apirogeni crimpati HUAYI", "pz", "Flaconi sterili apirogeni crimpati HUAYI", "PYL", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("4380", "Capsule sterili HUAYI", "Capsule sterili HUAYI", "pz", "Capsule sterili HUAYI", "PYL", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("605", "Piastre TSA 55 mm", "Piastre TSA 55 mm", "pz", "Piastre TSA 55 mm", "PYL", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("606", "Piastre TSA 90 mm", "Piastre TSA 90 mm", "pz", "Piastre TSA 90 mm", "PYL", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("424", "Acqua arricchita [18O]H2O", "Acqua arricchita [18O]H2O", "g", "Acqua arricchita [18O]H2O", "PYL", "", "NO", "NO", 0.0, 999, "Reagenti")
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
    print("--- [TEST SUCCESSO: Picking PYL] ---")
    conn.close()

if __name__ == '__main__':
    run_test()
