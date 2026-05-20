import sqlite3

conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

query = """
WITH OldestActiveLot AS (
    SELECT 
        codice_mp,
        lotto_interno,
        giacenza,
        data_scadenza,
        ROW_NUMBER() OVER (
            PARTITION BY codice_mp 
            ORDER BY data_arrivo ASC, lotto_interno ASC
        ) as rn
    FROM Lotti_Interni
    WHERE giacenza IS NOT NULL AND CAST(giacenza AS FLOAT) > 0
)
SELECT 
    M.codice, 
    M.nome_mp, 
    M.scorta_minima,
    M.ordine_magazzino,
    M.categoria_magazzino,
    SUM(CASE WHEN L.giacenza IS NOT NULL THEN CAST(L.giacenza AS FLOAT) ELSE 0 END) as giacenza_totale,
    COUNT(CASE WHEN L.lotto_interno IS NOT NULL THEN 1 END) as num_lotti,
    MIN(CASE WHEN L.data_scadenza != "" THEN L.data_scadenza END) as prossima_scadenza,
    O.lotto_interno as lotto_in_uso,
    O.giacenza as lotto_in_uso_giacenza,
    O.data_scadenza as lotto_in_uso_scadenza
FROM Elenco_MP M
LEFT JOIN Lotti_Interni L ON M.codice = L.codice_mp
LEFT JOIN OldestActiveLot O ON M.codice = O.codice_mp AND O.rn = 1
GROUP BY M.codice, M.nome_mp, M.scorta_minima, M.ordine_magazzino, M.categoria_magazzino, O.lotto_interno, O.giacenza, O.data_scadenza
ORDER BY M.ordine_magazzino ASC, M.nome_mp ASC
"""

cursor.execute(query)
rows = cursor.fetchall()
print(f"Total rows fetched: {len(rows)}")
for r in rows[:10]:
    print(r)

conn.close()
