import sqlite3

conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

# Get all materials with their total giacenza
cursor.execute("""
    SELECT M.codice, M.nome_mp, SUM(CASE WHEN L.giacenza IS NOT NULL THEN CAST(L.giacenza AS FLOAT) ELSE 0 END) as giacenza_totale
    FROM Elenco_MP M
    LEFT JOIN Lotti_Interni L ON M.codice = L.codice_mp
    GROUP BY M.codice, M.nome_mp
""")
materials = cursor.fetchall()

print("Current total stocks:")
for m in materials:
    print(f"Code: {m[0]}, Name: {m[1]}, Stock: {m[2]}")

# We will set scorta_minima for a few items:
# 1. Etanolo (Code '2073', Stock: 200.0) -> Set scorta_minima to 250.0
# 2. Kit reagenti FET (Code '5611', Stock: 198.0) -> Set scorta_minima to 220.0
# 3. Precursore FET (Code '5614', Stock: 98.0) -> Set scorta_minima to 150.0

updates = [
    ('2073', 250.0),
    ('5611', 220.0),
    ('5614', 150.0)
]

for code, min_stock in updates:
    cursor.execute("UPDATE Elenco_MP SET scorta_minima = ? WHERE codice = ?", (min_stock, code))
    print(f"Updated {code} scorta_minima to {min_stock}")

conn.commit()

# Verify updates
cursor.execute("SELECT codice, nome_mp, scorta_minima FROM Elenco_MP WHERE codice IN ('2073', '5611', '5614')")
print("\nVerified minimum stock levels:")
for r in cursor.fetchall():
    print(r)

conn.close()
