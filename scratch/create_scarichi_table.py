import sqlite3
import os

db_path = os.path.join('database', 'database.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create Scarichi table
cursor.execute('''
CREATE TABLE IF NOT EXISTS Scarichi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    lotto_interno TEXT,
    causale TEXT,
    lotto_prod TEXT,
    quantita FLOAT,
    operatore TEXT,
    materiale_codice TEXT,
    controcampione_lotto TEXT,
    FOREIGN KEY (lotto_interno) REFERENCES Lotti_Interni(lotto_interno),
    FOREIGN KEY (materiale_codice) REFERENCES Elenco_MP(codice)
)
''')

conn.commit()
print("Table 'Scarichi' created successfully.")
conn.close()
