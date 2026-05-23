import sqlite3
from flask import request, jsonify
from db_utils import get_db_connection

def register_search_routes(app):
    @app.route('/api/search')
    def api_search():
        query = request.args.get('q', '').strip()
        if not query or len(query) < 2:
            return jsonify({
                'success': True,
                'results': {
                    'materie_prime': [],
                    'lotti': []
                }
            })
        
        conn = get_db_connection()
        try:
            # 1. Ricerca Materie Prime (per Nome o Codice)
            # Calcola anche la giacenza totale attiva dei lotti non chiusi
            mp_rows = conn.execute('''
                SELECT M.codice, M.nome_mp, M.unita_misura, M.categoria_magazzino, M.scorta_minima,
                       SUM(CASE 
                           WHEN L.giacenza IS NOT NULL AND L.giacenza != '' AND (L.chiuso IS NULL OR (L.chiuso != 'SI' AND L.chiuso != 'X'))
                           THEN CAST(L.giacenza AS FLOAT) 
                           ELSE 0 
                       END) as giacenza_totale
                FROM Elenco_MP M
                LEFT JOIN Lotti_Interni L ON M.codice = L.codice_mp
                WHERE M.nome_mp LIKE ? OR M.codice LIKE ?
                GROUP BY M.codice, M.nome_mp, M.unita_misura, M.categoria_magazzino, M.scorta_minima
                LIMIT 5
            ''', ('%' + query + '%', '%' + query + '%')).fetchall()
            
            materie_prime = []
            for r in mp_rows:
                item = dict(r)
                # Arrotonda la giacenza totale a 2 decimali
                item['giacenza_totale'] = round(item['giacenza_totale'] or 0.0, 2)
                materie_prime.append(item)
                
            # 2. Ricerca Lotti (per Lotto Interno o Lotto Fornitore)
            # Prende anche il nome della materia prima associata
            lotti_rows = conn.execute('''
                SELECT L.lotto_interno, L.lotto_fornitore, L.codice_mp, L.giacenza, L.data_scadenza, L.appr, M.nome_mp, M.unita_misura
                FROM Lotti_Interni L
                LEFT JOIN Elenco_MP M ON L.codice_mp = M.codice
                WHERE L.lotto_interno LIKE ? OR L.lotto_fornitore LIKE ?
                ORDER BY L.data_arrivo DESC
                LIMIT 5
            ''', ('%' + query + '%', '%' + query + '%')).fetchall()
            
            lotti = [dict(r) for r in lotti_rows]
            
            return jsonify({
                'success': True,
                'results': {
                    'materie_prime': [
                        {
                            'codice': m['codice'],
                            'nome_mp': m['nome_mp'],
                            'unita_misura': m['unita_misura'],
                            'categoria_magazzino': m['categoria_magazzino'] or 'Altro',
                            'giacenza_totale': m['giacenza_totale'],
                            'scorta_minima': float(m['scorta_minima']) if m['scorta_minima'] is not None else 0.0
                        } for m in materie_prime
                    ],
                    'lotti': [
                        {
                            'lotto_interno': l['lotto_interno'],
                            'lotto_fornitore': l['lotto_fornitore'] or '-',
                            'codice_mp': l['codice_mp'],
                            'nome_mp': l['nome_mp'] or 'Sconosciuta',
                            'giacenza': l['giacenza'] or '0',
                            'unita_misura': l['unita_misura'] or '',
                            'data_scadenza': l['data_scadenza'] or '-',
                            'appr': l['appr'] or '-'
                        } for l in lotti
                    ]
                }
            })
            
        except Exception as e:
            app.logger.error(f"Errore durante la ricerca spotlight: {e}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500
        finally:
            conn.close()
