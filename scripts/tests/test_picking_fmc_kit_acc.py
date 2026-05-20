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
    print("--- [TEST START: Picking FMC KIT ACC] ---")
    
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
        ("2266", "Colina cassetta Synthera per distillazione", "Colina cassetta Synthera per distillazione", "pz", "Colina cassetta Synthera per distillazione", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Kit"),
        ("2267", "Colina cassetta Synthera per alchinazione", "Colina cassetta Synthera per alchinazione", "pz", "Colina cassetta Synthera per alchinazione", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Kit"),
        ("2070", "Resin cartridge Se (QMA colina)", "Resin cartridge Se (QMA colina)", "pz", "Resin cartridge Se (QMA colina)", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Cartucce"),
        ("2263", "Cartucce Silica", "Cartucce Silica", "pz", "Cartucce Silica", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Cartucce"),
        ("2264", "HLB cartucce", "HLB cartucce", "pz", "HLB cartucce", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Cartucce"),
        ("2265", "Acell Plus CM (Colina)", "Acell Plus CM (Colina)", "pz", "Acell Plus CM (Colina)", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Cartucce"),
        ("2046", "Cryptand Solution", "Cryptand Solution", "ml", "Cryptand Solution", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("4663", "Kit accessori colina", "Kit accessori colina", "pz", "Kit accessori colina", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Kit"),
        ("2273", "DMAE", "DMAE", "ml", "DMAE", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("2073", "Etanolo", "Etanolo", "ml", "Etanolo", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("2072", "Acetonitrile", "Acetonitrile", "ml", "Acetonitrile", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("2071", "Dibromomethane", "Dibromomethane", "ml", "Dibromomethane", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("3209", "Ammoniaca (colina)", "Ammoniaca (colina)", "ml", "Ammoniaca (colina)", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("3099", "Vial da 10 ml", "Vial da 10 ml", "pz", "Vial da 10 ml", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("3094", "Vial da 4,5 ml", "Vial da 4,5 ml", "pz", "Vial da 4,5 ml", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("3096", "Vial da 4 ml", "Vial da 4 ml", "pz", "Vial da 4 ml", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("3095", "Setti da 13 mm", "Setti da 13 mm", "pz", "Setti da 13 mm", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("3097", "Setti da 11 mm", "Setti da 11 mm", "pz", "Setti da 11 mm", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("461", "Kit di frazionamento", "Kit di frazionamento", "pz", "Kit di frazionamento", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Kit"),
        ("701", "Sodio cloruro 0,9% (250 ml)", "Sodio cloruro 0,9% (250 ml)", "pz", "Sodio cloruro 0,9% (250 ml)", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Reagenti"),
        ("4379", "Flaconi sterili apirogeni crimpati HUAYI", "Flaconi sterili apirogeni crimpati HUAYI", "pz", "Flaconi sterili apirogeni crimpati HUAYI", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("4380", "Capsule sterili HUAYI", "Capsule sterili HUAYI", "pz", "Capsule sterili HUAYI", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("2395", "Filtri STERIFIX", "Filtri STERIFIX", "pz", "Filtri STERIFIX", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Filtri"),
        ("1368", "Filtro Millex OR 0.22 micron", "Filtro Millex OR 0.22 micron", "pz", "Filtro Millex OR 0.22 micron", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Filtri"),
        ("605", "Piastre TSA 55 mm", "Piastre TSA 55 mm", "pz", "Piastre TSA 55 mm", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("606", "Piastre TSA 90 mm", "Piastre TSA 90 mm", "pz", "Piastre TSA 90 mm", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Consumabili"),
        ("424", "Acqua arricchita [18O]H2O", "Acqua arricchita [18O]H2O", "g", "Acqua arricchita [18O]H2O", "FMC KIT ACC", "", "NO", "NO", 0.0, 999, "Reagenti")
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
    print("--- [TEST SUCCESSO: Picking FMC KIT ACC] ---")
    conn.close()

if __name__ == '__main__':
    run_test()
