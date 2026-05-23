import sqlite3
from datetime import datetime
from flask import render_template, request, jsonify
from db_utils import get_db_connection, log_audit

def register_etichette_routes(app):
    @app.route('/nuova_etichetta')
    def nuova_etichetta():
        conn = get_db_connection()
        try:
            lotti_rows = conn.execute('''
                SELECT L.lotto_interno, L.data_arrivo, L.lotto_fornitore, L.fornitore, L.data_scadenza, L.qnt_arrivata, L.giacenza, L.data_approvazione,
                       L.data_consegna_qc, L.appr,
                       M.codice as codice_mp, M.nome_mp, M.unita_misura
            FROM Lotti_Interni L
            JOIN Elenco_MP M ON L.codice_mp = M.codice
            WHERE (L.chiuso IS NULL OR (L.chiuso != 'SI' AND L.chiuso != 'X'))
            ORDER BY L.data_arrivo DESC, L.lotto_interno DESC
            ''').fetchall()
            lotti = [dict(row) for row in lotti_rows]

            printed_rows = conn.execute('SELECT lotto_interno, tipo_stampa FROM Storico_Etichette').fetchall()
            printed_map = {}
            for row in printed_rows:
                lotto = row['lotto_interno']
                tipo = row['tipo_stampa']
                if lotto not in printed_map:
                    printed_map[lotto] = set()
                printed_map[lotto].add(tipo)

            for lot in lotti:
                lotto_id = lot['lotto_interno']
                lot['printed_bianco'] = 'BIANCO' in printed_map.get(lotto_id, set())
                lot['printed_verde'] = 'VERDE' in printed_map.get(lotto_id, set())

        except Exception as e:
            app.logger.error(f"Errore nel recupero dei lotti per le etichette: {e}", exc_info=True)
            lotti = []
        finally:
            conn.close()
        
        return render_template('nuova_etichetta.html', lotti=lotti)

    @app.route('/storico_etichetta')
    def storico_etichetta():
        conn = get_db_connection()
        try:
            rows = conn.execute('''
                SELECT S.id, S.data_ora, S.lotto_interno, S.codice_mp, S.nome_mp, S.data_arrivo, S.quantita, S.tipo_stampa, S.operatore,
                       L.lotto_fornitore, L.data_scadenza, L.data_approvazione
                FROM Storico_Etichette S
                LEFT JOIN Lotti_Interni L ON S.lotto_interno = L.lotto_interno
                ORDER BY S.id DESC
            ''').fetchall()
            etichette = [dict(row) for row in rows]
        except Exception as e:
            app.logger.error(f"Errore nel recupero dello storico etichette: {e}", exc_info=True)
            etichette = []
        finally:
            conn.close()
        return render_template('storico_etichetta.html', etichette=etichette)

    @app.route('/api/salva_etichetta', methods=['POST'])
    def api_salva_etichetta():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'Dati mancanti'}), 400
                
            lotto_interno = data.get('lotto_interno')
            nome_mp = data.get('nome_mp')
            codice_mp = data.get('codice_mp')
            data_arrivo = data.get('data_arrivo')
            quantita = data.get('quantita')
            tipo_stampa = data.get('tipo_stampa', 'GIALLO')
            operatore = "Sistema"
            
            if not lotto_interno or not nome_mp:
                return jsonify({'success': False, 'message': 'Lotto interno e nome prodotto obbligatori'}), 400
                
            data_ora = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
            
            conn = get_db_connection()
            
            existing = conn.execute('''
                SELECT 1 FROM Storico_Etichette 
                WHERE lotto_interno = ? AND tipo_stampa = ?
            ''', (lotto_interno, tipo_stampa)).fetchone()
            
            if existing:
                conn.close()
                return jsonify({'success': False, 'message': 'Un\'etichetta di questo tipo è già stata stampata per questo lotto.'}), 400
                
            if tipo_stampa == 'VERDE':
                bianca_exists = conn.execute('''
                    SELECT 1 FROM Storico_Etichette
                    WHERE lotto_interno = ? AND tipo_stampa = 'BIANCO'
                ''', (lotto_interno,)).fetchone()
                if not bianca_exists:
                    conn.close()
                    return jsonify({'success': False, 'message': "Impossibile stampare l'etichetta verde se l'etichetta bianca non è stata ancora generata."}), 400
                    
                lot_info = conn.execute('''
                    SELECT data_consegna_qc, appr FROM Lotti_Interni
                    WHERE lotto_interno = ?
                ''', (lotto_interno,)).fetchone()
                if not lot_info:
                    conn.close()
                    return jsonify({'success': False, 'message': "Lotto non trovato."}), 404
                    
                data_qc = lot_info['data_consegna_qc']
                appr_val = lot_info['appr']
                
                if not data_qc or data_qc == '-':
                    conn.close()
                    return jsonify({'success': False, 'message': "Impossibile stampare l'etichetta verde se il QC non è ancora stato impostato (data consegna QC mancante)."}), 400
                    
                if not appr_val or appr_val.upper() != 'OK':
                    conn.close()
                    return jsonify({'success': False, 'message': "Impossibile stampare l'etichetta verde se il lotto non è stato ancora approvato (Appr. deve essere OK)."}), 400
                
            conn.execute('''
                INSERT INTO Storico_Etichette (data_ora, lotto_interno, codice_mp, nome_mp, data_arrivo, quantita, tipo_stampa, operatore)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data_ora, lotto_interno, codice_mp, nome_mp, data_arrivo, quantita, tipo_stampa, operatore))
            
            if tipo_stampa == 'VERDE':
                conn.execute('''
                    UPDATE Lotti_Interni
                    SET etich = 'OK'
                    WHERE lotto_interno = ?
                ''', (lotto_interno,))
                
            log_audit(
                azione=f"Generata Etichetta ({tipo_stampa})",
                tabella_interessata="Storico_Etichette",
                operatore=operatore,
                vecchio_valore=None,
                nuovo_valore={
                    'lotto_interno': lotto_interno,
                    'nome_mp': nome_mp,
                    'codice_mp': codice_mp,
                    'tipo_stampa': tipo_stampa
                },
                conn=conn
            )
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Etichetta salvata nello storico'})
        except Exception as e:
            app.logger.error(f"Errore durante il salvataggio dell'etichetta: {e}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/api/lotto_etichette_timestamps/<path:lotto_interno>')
    def api_lotto_etichette_timestamps(lotto_interno):
        conn = get_db_connection()
        try:
            rows = conn.execute('''
                SELECT tipo_stampa, data_ora 
                FROM Storico_Etichette 
                WHERE lotto_interno = ?
                ORDER BY id ASC
            ''', (lotto_interno,)).fetchall()
            
            timestamps = {
                'BIANCO': None,
                'VERDE': None
            }
            for row in rows:
                tipo = row['tipo_stampa']
                if tipo in timestamps:
                    if not timestamps[tipo]:
                        timestamps[tipo] = row['data_ora']
                        
            return jsonify({
                'success': True,
                'lotto_interno': lotto_interno,
                'bianco': timestamps['BIANCO'],
                'verde': timestamps['VERDE']
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            conn.close()
