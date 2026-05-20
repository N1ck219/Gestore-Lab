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
    print("--- [TEST START: Picking FET] ---")
    
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
        ("5612", "Kit Hardware FET", "Kit Hardware FET", "pz", "Kit Hardware FET", "FET", "", "NO", "NO", 0.0, 999, "Kit"),
        ("5611", "Kit reagenti FET", "Kit reagenti FET", "pz", "Kit reagenti FET", "FET", "", "NO", "NO", 0.0, 999, "Kit"),
        ("5614", "Precursore FET", "Precursore FET", "pz", "Precursore FET", "FET", "", "NO", "NO", 0.0, 999, "Kit"),
        ("5613", "QMA Eluent FET (2-8°C)", "QMA Eluent FET (2-8°C)", "pz", "QMA Eluent FET (2-8°C)", "FET", "", "NO", "NO", 0.0, 999, "Kit"),
        ("2073", "Etanolo", "Etanolo", "ml", "Etanolo", "FET", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("4486", "Acqua PPI Bottiglia 1L", "Acqua PPI Bottiglia 1L", "pz", "Acqua PPI Bottiglia 1L", "FET", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("5686", "Sodio Cloruro 0,9% Bottiglia 250ml", "Sodio Cloruro 0,9% Bottiglia 250ml", "pz", "Sodio Cloruro 0,9% Bottiglia 250ml", "FET", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("5659", "Sodio Cloruro 0,9% Bag 250ml", "Sodio Cloruro 0,9% Bag 250ml", "pz", "Sodio Cloruro 0,9% Bag 250ml", "FET", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("5679", "Strip Acido Ascorbico", "Strip Acido Ascorbico", "pz", "Strip Acido Ascorbico", "FET", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("3136", "Sodio Ascorbato", "Sodio Ascorbato", "g", "Sodio Ascorbato", "FET", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("461", "Kit di frazionamento", "Kit di frazionamento", "pz", "Kit di frazionamento", "FET", "", "NO", "NO", 0.0, 999, "Kit"),
        ("701", "Sodio cloruro 0,9% (250 ml)", "Sodio cloruro 0,9% (250 ml)", "pz", "Sodio cloruro 0,9% (250 ml)", "FET", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("2691", "Filtro Millex GP", "Filtro Millex GP", "pz", "Filtro Millex GP", "FET", "", "NO", "NO", 0.0, 999, "Filtri"),
        ("5584", "Filtro Pall", "Filtro Pall", "pz", "Filtro Pall", "FET", "", "NO", "NO", 0.0, 999, "Filtri"),
        ("4379", "Flaconi sterili apirogeni crimpati HUAYI", "Flaconi sterili apirogeni crimpati HUAYI", "pz", "Flaconi sterili apirogeni crimpati HUAYI", "FET", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("4380", "Capsule sterili HUAYI", "Capsule sterili HUAYI", "pz", "Capsule sterili HUAYI", "FET", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("605", "Piastre TSA 55 mm", "Piastre TSA 55 mm", "pz", "Piastre TSA 55 mm", "FET", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("606", "Piastre TSA 90 mm", "Piastre TSA 90 mm", "pz", "Piastre TSA 90 mm", "FET", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("424", "Acqua arricchita [18O]H2O", "Acqua arricchita [18O]H2O", "g", "Acqua arricchita [18O]H2O", "FET", "", "NO", "NO", 0.0, 999, "Reagenti")
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
    print("--- [TEST SUCCESSO: Picking FET] ---")
    conn.close()

if __name__ == '__main__':
    run_test()
