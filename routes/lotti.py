import os
import re
import sqlite3
from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash
from db_utils import get_db_connection, log_audit
from pdf_utils import genera_pdf_distribuzione, genera_pdf_richiesta_analisi
from config import LISTA_DISTRIBUZIONE_DIR, RICHIESTA_ANALISI_DIR

def register_lotti_routes(app):
    @app.route('/lotti')
    def lotti_list():
        conn = get_db_connection()
        lotti_rows = conn.execute('''
            SELECT L.*, M.nome_mp,
                   (SELECT COUNT(*) FROM Storico_Etichette S WHERE S.lotto_interno = L.lotto_interno AND S.tipo_stampa = 'BIANCO') as has_bianco,
                   (SELECT COUNT(*) FROM Storico_Etichette S WHERE S.lotto_interno = L.lotto_interno AND S.tipo_stampa = 'VERDE') as has_verde
            FROM Lotti_Interni L 
            LEFT JOIN Elenco_MP M ON L.codice_mp = M.codice 
            ORDER BY L.data_arrivo DESC
        ''').fetchall()
        lotti = [dict(row) for row in lotti_rows]
        
        # Carichiamo anche le materie prime per il menu a tendina nel modal di modifica
        materie = conn.execute('SELECT codice, nome_mp FROM Elenco_MP ORDER BY nome_mp ASC').fetchall()
        
        conn.close()
        return render_template('lotti_list.html', lotti=lotti, materie=materie)

    @app.route('/update_lotto', methods=['POST'])
    def update_lotto():
        conn = get_db_connection()
        data = {
            'codice_mp': request.form['codice_mp'],
            'data_arrivo': request.form['data_arrivo'],
            'lotto_fornitore': request.form['lotto_fornitore'],
            'fornitore': request.form['fornitore'],
            'data_scadenza': request.form['data_scadenza'],
            'qnt_arrivata': request.form['qnt_arrivata'],
            'pz_x_cf': request.form['pz_x_cf'],
            'giacenza': request.form['giacenza'],
            'data_consegna_qc': request.form['data_consegna_qc'],
            'data_approvazione': request.form['data_approvazione'],
            'arrivo_magazzino': request.form['arrivo_magazzino'],
            'consumi': request.form['consumi'],
            'ca': request.form['ca'],
            'reparto': request.form['reparto'],
            'appr': request.form['appr'],
            'etich': request.form['etich'],
            'cc': request.form['cc'],
            'codice_lotto': request.form['codice_lotto'],
            'lotto_interno': request.form['lotto_interno'] # Chiave per WHERE
        }
        
        # Logica automatica bidirezionale per Appr
        if data['data_approvazione'] and data['data_approvazione'].strip():
            data['appr'] = 'OK'
        else:
            data['appr'] = '-'
        
        try:
            old_row = conn.execute("SELECT * FROM Lotti_Interni WHERE lotto_interno = ?", (data['lotto_interno'],)).fetchone()
            old_val = dict(old_row) if old_row else None

            conn.execute('''UPDATE Lotti_Interni SET 
                            codice_mp=?, data_arrivo=?, lotto_fornitore=?, fornitore=?, data_scadenza=?, 
                            qnt_arrivata=?, pz_x_cf=?, giacenza=?, data_consegna_qc=?, data_approvazione=?, 
                            arrivo_magazzino=?, consumi=?, ca=?, reparto=?, appr=?, etich=?, cc=?, codice_lotto=?
                            WHERE lotto_interno=?''',
                         (data['codice_mp'], data['data_arrivo'], data['lotto_fornitore'], data['fornitore'], 
                          data['data_scadenza'], data['qnt_arrivata'], data['pz_x_cf'], data['giacenza'], 
                          data['data_consegna_qc'], data['data_approvazione'], data['arrivo_magazzino'], 
                          data['consumi'], data['ca'], data['reparto'], data['appr'], data['etich'], 
                          data['cc'], data['codice_lotto'], data['lotto_interno']))
            
            log_audit(
                azione="MODIFICA",
                tabella_interessata="Lotti_Interni",
                operatore="Sistema",
                vecchio_valore=old_val,
                nuovo_valore=data,
                conn=conn
            )
            
            conn.commit()
            flash('Lotto aggiornato con successo!')
        except Exception as e:
            flash(f'Errore durante l\'aggiornamento: {e}')
        finally:
            conn.close()
        
        return redirect(url_for('lotti_list'))

    @app.route('/add_lotto', methods=('GET', 'POST'))
    def add_lotto():
        today = date.today().strftime('%d-%m-%Y')
        conn = get_db_connection()
        materie = conn.execute('SELECT codice, nome_mp FROM Elenco_MP ORDER BY nome_mp ASC').fetchall()
        fornitori = conn.execute('SELECT nome FROM Fornitori ORDER BY nome ASC').fetchall()
        
        if request.method == 'POST':
            data = {
                'lotto_interno': request.form.get('lotto_interno'),
                'codice_mp': request.form.get('codice_mp'),
                'mp_search': request.form.get('mp_search'),
                'data_arrivo': request.form.get('data_arrivo'),
                'lotto_fornitore': request.form.get('lotto_fornitore'),
                'fornitore': request.form.get('fornitore'),
                'data_scadenza': request.form.get('data_scadenza'),
                'qnt_arrivata': request.form.get('qnt_arrivata'),
                'pz_x_cf': request.form.get('pz_x_cf'),
                'giacenza': request.form.get('qnt_arrivata'),
                'in_uso': 'SI'
            }
            
            required_db_fields = ['lotto_interno', 'codice_mp', 'data_arrivo', 'lotto_fornitore', 'fornitore', 'data_scadenza', 'qnt_arrivata', 'pz_x_cf']
            
            # Validazione lato server
            errors = []
            
            # A. Controllo campi obbligatori
            if not all(data[f] for f in required_db_fields):
                errors.append("Tutti i campi sono obbligatori!")
            else:
                # B. Verifica data scadenza non precedente a data arrivo
                try:
                    arr_dt = datetime.strptime(data['data_arrivo'], '%Y-%m-%d').date()
                    scad_dt = datetime.strptime(data['data_scadenza'], '%Y-%m-%d').date()
                    if scad_dt < arr_dt:
                        errors.append("La Data di Scadenza non può essere precedente alla Data di Arrivo.")
                except ValueError:
                    errors.append("Le date inserite non sono in un formato valido.")
                    
                # C. Verifica quantità arrivata > 0
                try:
                    qnt_str = data['qnt_arrivata'].replace(',', '.')
                    qnt = float(qnt_str)
                    if qnt <= 0:
                        errors.append("La Quantità Arrivata deve essere maggiore di zero.")
                except ValueError:
                    errors.append("La Quantità Arrivata deve essere un numero valido.")
                    
                # D. Verifica pezzi per confezione > 0
                try:
                    pz = int(data['pz_x_cf'])
                    if pz <= 0:
                        errors.append("I Pezzi per confezione devono essere maggiori di zero.")
                except ValueError:
                    errors.append("I Pezzi per confezione devono essere un numero intero valido.")
            
            if errors:
                error_msg = "Problemi di validazione: " + " | ".join(errors)
                flash(error_msg, 'error')
                return render_template('add_lotto.html', materie=materie, fornitori=fornitori, today=today, form_data=data)
            else:
                try:
                    conn.execute('''INSERT INTO Lotti_Interni 
                                    (lotto_interno, codice_mp, data_arrivo, lotto_fornitore, fornitore, data_scadenza, 
                                     qnt_arrivata, pz_x_cf, giacenza, in_uso) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                 (data['lotto_interno'], data['codice_mp'], data['data_arrivo'], 
                                  data['lotto_fornitore'], data['fornitore'], data['data_scadenza'],
                                  data['qnt_arrivata'], data['pz_x_cf'], data['giacenza'], data['in_uso']))
                    
                    log_audit(
                        azione="INSERIMENTO",
                        tabella_interessata="Lotti_Interni",
                        operatore="Sistema",
                        nuovo_valore=data,
                        conn=conn
                    )
                    
                    conn.commit()
                    flash('Lotto aggiunto con successo!')
                    return redirect(url_for('lotti_list'))
                except sqlite3.IntegrityError:
                    flash(f'Errore: Il lotto {data["lotto_interno"]} esiste già nel database!')
                    return render_template('add_lotto.html', materie=materie, fornitori=fornitori, today=today, form_data=data)
                finally:
                    conn.close()

        conn.close()
        return render_template('add_lotto.html', materie=materie, fornitori=fornitori, today=today)

    @app.route('/api/lotti_per_mp/<codice>')
    def api_lotti_per_mp(codice):
        conn = get_db_connection()
        lotti_rows = conn.execute('''
            SELECT 
                arrivo_magazzino, 
                data_arrivo,
                lotto_interno, 
                lotto_fornitore, 
                qnt_arrivata, 
                data_scadenza,
                giacenza,
                (SELECT MAX(data) FROM Scarichi WHERE lotto_interno = L.lotto_interno) as ultimo_utilizzo
            FROM Lotti_Interni L
            WHERE codice_mp = ? 
            ORDER BY data_arrivo DESC, lotto_interno DESC
        ''', (codice,)).fetchall()
        
        lotti = [dict(row) for row in lotti_rows]
        
        oldest_active_lotto_interno = None
        oldest_active_date = None
        
        for lot in lotti:
            try:
                giac = float(lot['giacenza']) if lot['giacenza'] is not None else 0.0
            except ValueError:
                giac = 0.0
                
            if giac > 0:
                arr_date = lot['data_arrivo'] or ''
                lot_id = lot['lotto_interno'] or ''
                if oldest_active_date is None or arr_date < oldest_active_date or (arr_date == oldest_active_date and lot_id < oldest_active_lotto_interno):
                    oldest_active_date = arr_date
                    oldest_active_lotto_interno = lot_id
                    
        for lot in lotti:
            lot['in_uso'] = (lot['lotto_interno'] == oldest_active_lotto_interno) if oldest_active_lotto_interno else False
            
        conn.close()
        return {'lotti': lotti}

    @app.route('/api/approva_lotto', methods=['POST'])
    def api_approva_lotto():
        data_json = request.get_json()
        if not data_json:
            return {'success': False, 'message': 'Dati mancanti'}, 400
        
        lotto_interno = data_json.get('lotto_interno')
        data_approvazione = data_json.get('data_approvazione')
        
        if not lotto_interno or not data_approvazione:
            return {'success': False, 'message': 'Campi obbligatori mancanti'}, 400
        
        conn = get_db_connection()
        try:
            old_row = conn.execute("SELECT * FROM Lotti_Interni WHERE lotto_interno = ?", (lotto_interno,)).fetchone()
            old_val = dict(old_row) if old_row else None

            conn.execute('''
                UPDATE Lotti_Interni 
                SET data_approvazione = ?, appr = 'OK' 
                WHERE lotto_interno = ?
            ''', (data_approvazione, lotto_interno))
            
            new_val = dict(old_val) if old_val else {}
            new_val['data_approvazione'] = data_approvazione
            new_val['appr'] = 'OK'
            
            log_audit(
                azione="APPROVAZIONE_QC",
                tabella_interessata="Lotti_Interni",
                operatore="Sistema",
                vecchio_valore=old_val,
                nuovo_valore=new_val,
                conn=conn
            )
            
            conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}, 500
        finally:
            conn.close()

    @app.route('/api/cc_info/<lotto_interno>')
    def api_cc_info(lotto_interno):
        conn = get_db_connection()
        try:
            row = conn.execute('''
                SELECT data, operatore 
                FROM Scarichi 
                WHERE lotto_interno = ? AND causale = 'Controcampione' 
                ORDER BY data DESC LIMIT 1
            ''', (lotto_interno,)).fetchone()
            
            if row:
                return {
                    'success': True,
                    'found': True,
                    'data': row['data'],
                    'operatore': row['operatore']
                }
            else:
                return {
                    'success': True,
                    'found': False
                }
        except Exception as e:
            return {'success': False, 'message': str(e)}, 500
        finally:
            conn.close()

    @app.route('/api/aggiungi_attesa_qc/<lotto_interno>', methods=['POST'])
    def api_aggiungi_attesa_qc(lotto_interno):
        conn = get_db_connection()
        try:
            old_row = conn.execute("SELECT * FROM Lotti_Interni WHERE lotto_interno = ?", (lotto_interno,)).fetchone()
            if not old_row:
                return {'success': False, 'message': 'Lotto non trovato'}, 404
            old_val = dict(old_row)

            conn.execute("UPDATE Lotti_Interni SET qc_attesa = 'SI' WHERE lotto_interno = ?", (lotto_interno,))
            
            new_val = dict(old_val)
            new_val['qc_attesa'] = 'SI'
            
            log_audit(
                azione="AGGIUNGI_ATTESA_QC",
                tabella_interessata="Lotti_Interni",
                operatore="Sistema",
                vecchio_valore=old_val,
                nuovo_valore=new_val,
                conn=conn
            )
            conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}, 500
        finally:
            conn.close()

    @app.route('/api/rimuovi_attesa_qc/<lotto_interno>', methods=['POST'])
    def api_rimuovi_attesa_qc(lotto_interno):
        conn = get_db_connection()
        try:
            old_row = conn.execute("SELECT * FROM Lotti_Interni WHERE lotto_interno = ?", (lotto_interno,)).fetchone()
            if not old_row:
                return {'success': False, 'message': 'Lotto non trovato'}, 404
            old_val = dict(old_row)

            conn.execute("UPDATE Lotti_Interni SET qc_attesa = 'NO' WHERE lotto_interno = ?", (lotto_interno,))
            
            new_val = dict(old_val)
            new_val['qc_attesa'] = 'NO'
            
            log_audit(
                azione="RIMUOVI_ATTESA_QC",
                tabella_interessata="Lotti_Interni",
                operatore="Sistema",
                vecchio_valore=old_val,
                nuovo_valore=new_val,
                conn=conn
            )
            conn.commit()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}, 500
        finally:
            conn.close()

    @app.route('/api/genera_pdf_distribuzione/<lotto_interno>', methods=['POST'])
    def genera_pdf_distribuzione_route(lotto_interno):
        conn = get_db_connection()
        try:
            lotto_row = conn.execute('''
                SELECT L.*, M.nome_mp 
                FROM Lotti_Interni L 
                LEFT JOIN Elenco_MP M ON L.codice_mp = M.codice 
                WHERE L.lotto_interno = ?
            ''', (lotto_interno,)).fetchone()
            
            if not lotto_row:
                return {'success': False, 'message': 'Lotto non trovato'}, 404
                
            lotto_row = dict(lotto_row)
            
            scarichi_rows = conn.execute('''
                SELECT S.data, S.causale, S.quantita, S.operatore, S.lotto_prod, S.data_ultimo_utilizzo 
                FROM Scarichi S
                WHERE S.lotto_interno = ?
                ORDER BY S.data ASC, S.id ASC
            ''', (lotto_interno,)).fetchall()
            
            scarichi = [dict(row) for row in scarichi_rows]
            
            save_dir = LISTA_DISTRIBUZIONE_DIR
            if not os.path.isabs(save_dir):
                save_dir = os.path.join(app.root_path, save_dir)
            os.makedirs(save_dir, exist_ok=True)
            
            safe_lotto = re.sub(r'[\\/*?:"<>|]', '_', lotto_interno)
            filename = f"lista_distribuzione_{safe_lotto}.pdf"
            filepath = os.path.join(save_dir, filename)
            
            genera_pdf_distribuzione(lotto_interno, lotto_row, scarichi, filepath)
            
            return {'success': True, 'filename': filename, 'path': filepath}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}, 500
        finally:
            conn.close()

    @app.route('/api/stampa_richiesta_analisi', methods=['POST'])
    def api_stampa_richiesta_analisi():
        conn = get_db_connection()
        try:
            lotti_rows = conn.execute('''
                SELECT L.*, M.nome_mp, M.unita_misura
                FROM Lotti_Interni L
                LEFT JOIN Elenco_MP M ON L.codice_mp = M.codice
                WHERE L.qc_attesa = 'SI'
                ORDER BY L.data_arrivo DESC, L.lotto_interno DESC
            ''').fetchall()
            
            lotti = [dict(row) for row in lotti_rows]
            if not lotti:
                return {'success': False, 'message': 'Nessun lotto in lista di attesa.'}, 400
            
            save_dir = RICHIESTA_ANALISI_DIR
            if not os.path.isabs(save_dir):
                save_dir = os.path.join(app.root_path, save_dir)
            os.makedirs(save_dir, exist_ok=True)
            
            today_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"richiesta_analisi_{today_str}.pdf"
            filepath = os.path.join(save_dir, filename)
            
            genera_pdf_richiesta_analisi(lotti, filepath)
            
            today_iso = datetime.now().strftime('%Y-%m-%d')
            
            for lot in lotti:
                lotto_interno = lot['lotto_interno']
                
                old_row = conn.execute("SELECT * FROM Lotti_Interni WHERE lotto_interno = ?", (lotto_interno,)).fetchone()
                old_val = dict(old_row) if old_row else None
                
                conn.execute('''
                    UPDATE Lotti_Interni
                    SET data_consegna_qc = ?, qc_attesa = 'NO'
                    WHERE lotto_interno = ?
                ''', (today_iso, lotto_interno))
                
                new_val = dict(old_val) if old_val else {}
                new_val['data_consegna_qc'] = today_iso
                new_val['qc_attesa'] = 'NO'
                
                log_audit(
                    azione="STAMPA_RICHIESTA_QC",
                    tabella_interessata="Lotti_Interni",
                    operatore="Sistema",
                    vecchio_valore=old_val,
                    nuovo_valore=new_val,
                    conn=conn
                )
                
            conn.commit()
            return {'success': True, 'filename': filename}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}, 500
        finally:
            conn.close()
