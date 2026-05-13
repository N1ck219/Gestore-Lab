import sqlite3

ORDERED_DATA = [
    # GRUPPO 1: AZZURRO (Materiale Sterile)
    ("Vetro e Materiale sterile", [
        "Flaconi sterili apirogeni crimpati HUAYI",
        "Capsule sterili HUAYI",
        "Kit di frazionamento",
        "Kit aggiuntivo di frazionamento",
        "Filtro Millex OR 0.22 micron"
    ]),
    # GRUPPO 2: BIANCO (Consumo e Reagenti vari)
    ("Materiale di consumo e Reagenti vari", [
        "Acqua Arricchita Rigenerata",
        "Etanolo eccipiente",
        "Piastre per campionamento microbiologico",
        "Sodio Cloruro 10%",
        "Sodio cloruro 0,9% (250 ml)",
        "Kit Hardware FDG TRASIS",
        "Kit reagenti FDG TRASIS",
        "Mannosio Trifilato TRASIS",
        "Acqua PPI Bag 1L",
        "Chromabond FDG TRASIS"
    ]),
    # GRUPPO 3: ARANCIO (Kit Synthera)
    ("Kit IFP Synthera", [
        "Kit IFP Synthera",
        "Kit accessori Synthera",
        "Kit chimico reagenti Synthera",
        "Mannosio Trifilato Synthera",
        "Kit purificazione FBB",
        "Kit reagenti FBB",
        "Kit reagenti FBB (2-8°C)",
        "Filtro Minisart 0,22 micron"
    ]),
    # GRUPPO 4: VIOLA (Colina e Reagenti Chimici)
    ("Colina e Altri Reagenti", [
        "Colina cassetta Synthera per alchinazione",
        "Colina cassetta Synthera per distillazione",
        "Kit chimico caldo colina",
        "Kit chimico freddo colina",
        "Kit accessori colina",
        "Resin cartridge Se (QMA colina)",
        "Cartucce Silica",
        "HLB cartucce",
        "Acell Plus CM (Colina)",
        "Cryptand Solution",
        "Acido Cloridrico",
        "DMAE",
        "Filtri STERIFIX",
        "Etanolo",
        "Acetonitrile",
        "Sodio Idrogeno Carbonato",
        "Ammoniaca (colina)",
        "Dibromomethane",
        "Vial da 10 ml",
        "Vial da 4,5 ml",
        "Vial da 4 ml",
        "Setti da 13 mm",
        "Setti da 11 mm"
    ]),
    # GRUPPO 5: VERDE (DOPA e Finali)
    ("Prodotti DOPA e Finali", [
        "DOPA Trasis Cassette",
        "DOPA Trasis Kit 1 (2-8°C)",
        "DOPA Trasis Kit 2",
        "Acqua PPI Bottiglia 1L",
        "Acqua PPI Bottiglia 250ml",
        "Acqua PPI Bag 250ml",
        "DOPA Etanolo",
        "Acido ascorbico",
        "Acido acetico",
        "Sodio acetato triidrato",
        "Acqua arricchita [18O]H2O"
    ])
]

def update_order():
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    
    # Reset iniziale
    cursor.execute("UPDATE Elenco_MP SET ordine_magazzino = 999, categoria_magazzino = NULL")
    
    current_order = 1
    for cat_name, products in ORDERED_DATA:
        for prod_name in products:
            # Cerchiamo per corrispondenza parziale per essere sicuri di prenderli
            cursor.execute('''
                UPDATE Elenco_MP 
                SET ordine_magazzino = ?, categoria_magazzino = ? 
                WHERE nome_mp LIKE ?
            ''', (current_order, cat_name, f"%{prod_name}%"))
            current_order += 1
            
    conn.commit()
    conn.close()
    print("Ordinamento e categorie aggiornati correttamente.")

if __name__ == "__main__":
    update_order()
