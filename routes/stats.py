import sqlite3
from datetime import datetime
from flask import render_template, jsonify
from db_utils import get_db_connection

def register_stats_routes(app):
    @app.route('/statistiche')
    def statistiche():
        conn = get_db_connection()
        # 1. Recupero elenco materie prime per la select
        materie_rows = conn.execute('SELECT codice, nome_mp FROM Elenco_MP ORDER BY nome_mp ASC').fetchall()
        materie = [dict(row) for row in materie_rows]
        
        # 2. KPI 1: Totale scarichi registrati
        tot_scarichi = conn.execute('SELECT COUNT(*) FROM Scarichi').fetchone()[0]
        
        # 3. KPI 2: Lotti attivi in giacenza
        tot_lotti_attivi = conn.execute('SELECT COUNT(*) FROM Lotti_Interni WHERE CAST(giacenza AS FLOAT) > 0').fetchone()[0]
        
        # 4. KPI 3: Materia prima più consumata negli ultimi 30 giorni
        maggior_consumo_row = conn.execute('''
            SELECT M.nome_mp, SUM(S.quantita) as totale, M.unita_misura
            FROM Scarichi S
            JOIN Elenco_MP M ON S.materiale_codice = M.codice
            WHERE S.data >= date('now', '-30 days')
            GROUP BY S.materiale_codice
            ORDER BY totale DESC
            LIMIT 1
        ''').fetchone()
        maggior_consumo = dict(maggior_consumo_row) if maggior_consumo_row else None
        
        # 5. KPI 4: Prelievi eseguiti oggi
        prelievi_oggi = conn.execute('''
            SELECT COUNT(*) FROM Scarichi 
            WHERE data = date('now', 'localtime')
        ''').fetchone()[0]
        
        # 6. Top 5 Materie Prime più Consumate di Sempre
        top_materie_rows = conn.execute('''
            SELECT M.nome_mp, SUM(S.quantita) as totale
            FROM Scarichi S
            JOIN Elenco_MP M ON S.materiale_codice = M.codice
            GROUP BY S.materiale_codice
            ORDER BY totale DESC
            LIMIT 5
        ''').fetchall()
        top_materie = [dict(row) for row in top_materie_rows]
        
        # 7. Distribuzione delle Causali di Scarico
        causali_rows = conn.execute('''
            SELECT causale, COUNT(*) as conteggio
            FROM Scarichi
            GROUP BY causale
            ORDER BY conteggio DESC
        ''').fetchall()
        causali = [dict(row) for row in causali_rows]
        
        # 8. Lotti registrati per mese negli ultimi 6 mesi
        lotti_mensili_rows = conn.execute('''
            SELECT strftime('%Y-%m', data_arrivo) as mese, COUNT(*) as conteggio
            FROM Lotti_Interni
            WHERE data_arrivo >= date('now', '-6 months')
            GROUP BY mese
            ORDER BY mese ASC
        ''').fetchall()
        lotti_mensili = [dict(row) for row in lotti_mensili_rows]
        
        conn.close()
        
        return render_template(
            'statistiche.html',
            materie=materie,
            tot_scarichi=tot_scarichi,
            tot_lotti_attivi=tot_lotti_attivi,
            maggior_consumo=maggior_consumo,
            prelievi_oggi=prelievi_oggi,
            top_materie=top_materie,
            causali=causali,
            lotti_mensili=lotti_mensili
        )

    @app.route('/api/stats/consumi/<codice_mp>')
    def api_stats_consumi(codice_mp):
        conn = get_db_connection()
        # Query consumi degli ultimi 12 mesi per la materia selezionata
        rows = conn.execute('''
            SELECT strftime('%Y-%m', S.data) as mese, SUM(S.quantita) as totale, M.unita_misura, M.nome_mp
            FROM Scarichi S
            JOIN Elenco_MP M ON S.materiale_codice = M.codice
            WHERE S.materiale_codice = ? AND S.data >= date('now', '-12 months')
            GROUP BY mese
            ORDER BY mese ASC
        ''', (codice_mp,)).fetchall()
        
        dati = [dict(row) for row in rows]
        
        # Se non ci sono dati, restituiamo almeno informazioni di base per materia prima
        if not dati:
            mp_row = conn.execute('SELECT nome_mp, unita_misura FROM Elenco_MP WHERE codice = ?', (codice_mp,)).fetchone()
            if mp_row:
                dati = [{
                    'nome_mp': mp_row['nome_mp'],
                    'unita_misura': mp_row['unita_misura'],
                    'totale': 0.0,
                    'mese': datetime.now().strftime('%Y-%m')
                }]
                
        conn.close()
        return jsonify(dati)
