import os
import threading
import time
from datetime import datetime, timedelta
from flask import render_template, request, jsonify
from db_utils import get_db_connection

def register_main_routes(app):
    @app.template_filter('dateformat')
    def dateformat_filter(value, format='%d-%m-%Y'):
        if not value or value == '-':
            return value
        try:
            dt = datetime.strptime(value, '%Y-%m-%d')
            return dt.strftime(format)
        except:
            return value

    @app.template_filter('format_date')
    def format_date_filter(value):
        if not value:
            return ""
        try:
            if len(value) == 10 and value[2] == '-' and value[5] == '-':
                return value
            return datetime.strptime(value, '%Y-%m-%d').strftime('%d-%m-%Y')
        except:
            return value

    @app.route('/')
    def index():
        conn = get_db_connection()
        today = datetime.now().date()
        
        # 1. Recupera lotti attivi (con giacenza > 0)
        lotti_rows = conn.execute('''
            SELECT L.lotto_interno, L.codice_mp, L.giacenza, L.data_scadenza, L.lotto_fornitore, M.nome_mp 
            FROM Lotti_Interni L 
            JOIN Elenco_MP M ON L.codice_mp = M.codice 
            WHERE L.giacenza IS NOT NULL AND L.giacenza != '' AND CAST(L.giacenza AS FLOAT) > 0
              AND (L.chiuso IS NULL OR (L.chiuso != 'SI' AND L.chiuso != 'X'))
        ''').fetchall()
        
        lotti_scaduti = []
        lotti_in_scadenza = []
        
        def parse_db_date(date_str):
            if not date_str or date_str == '-':
                return None
            for fmt in ('%Y-%m-%d', '%d-%m-%Y'):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
            
        for row in lotti_rows:
            lot = dict(row)
            scad_date = parse_db_date(lot['data_scadenza'])
            if scad_date:
                if scad_date < today:
                    lotti_scaduti.append(lot)
                elif today <= scad_date <= today + timedelta(days=30):
                    lot['giorni_rimanenti'] = (scad_date - today).days
                    lotti_in_scadenza.append(lot)
                    
        # Ordinamento: per data di scadenza (più vecchi prima)
        lotti_scaduti.sort(key=lambda x: parse_db_date(x['data_scadenza']) or today)
        lotti_in_scadenza.sort(key=lambda x: parse_db_date(x['data_scadenza']) or today)
        
        # 2. Recupera materie prime sotto scorta minima
        inventory_rows = conn.execute('''
            SELECT M.codice, M.nome_mp, M.scorta_minima,
                   SUM(CASE WHEN L.giacenza IS NOT NULL AND L.giacenza != '' THEN CAST(L.giacenza AS FLOAT) ELSE 0 END) as giacenza_totale
            FROM Elenco_MP M
            LEFT JOIN Lotti_Interni L ON M.codice = L.codice_mp AND (L.chiuso IS NULL OR (L.chiuso != 'SI' AND L.chiuso != 'X'))
            GROUP BY M.codice, M.nome_mp, M.scorta_minima
        ''').fetchall()
        
        sotto_scorta = []
        for row in inventory_rows:
            item = dict(row)
            scorta_min = float(item['scorta_minima']) if item['scorta_minima'] is not None else 0.0
            if scorta_min > 0 and item['giacenza_totale'] < scorta_min:
                item['giacenza_totale'] = round(item['giacenza_totale'], 2)
                sotto_scorta.append(item)
                
        conn.close()
        
        return render_template('index.html', 
                               lotti_scaduti=lotti_scaduti, 
                               lotti_in_scadenza=lotti_in_scadenza, 
                               sotto_scorta=sotto_scorta)

    @app.route('/magazzino')
    def magazzino():
        conn = get_db_connection()
        inventory_rows = conn.execute('''
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
        ''').fetchall()
        
        inventory = [dict(row) for row in inventory_rows]
        
        grouped_inventory = {}
        for item in inventory:
            cat = item['categoria_magazzino'] or 'Altre Materie Prime'
            if cat not in grouped_inventory:
                grouped_inventory[cat] = []
            grouped_inventory[cat].append(item)
            
        conn.close()
        return render_template('magazzino.html', grouped_inventory=grouped_inventory)

    @app.route('/api/spegni', methods=['POST'])
    def api_spegni():
        app.logger.warning("Richiesta di spegnimento dell'applicazione Flask ricevuta ed in fase di elaborazione...")
        def kill_server():
            time.sleep(1.0)
            os._exit(0)
        threading.Thread(target=kill_server).start()
        return jsonify({'success': True, 'message': 'Arresto del server in corso... Puoi chiudere questa finestra.'})
