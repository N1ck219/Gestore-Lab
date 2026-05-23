import os
import sqlite3
from datetime import datetime, date
from flask import render_template, request, redirect, url_for, flash, jsonify
from db_utils import get_db_connection, log_audit
from pdf_utils import genera_pdf_picking
from config import PICKING_LIST_DIR

def register_scarichi_routes(app):
    @app.route('/scarico_manuale', methods=['GET', 'POST'])
    def scarico_manuale():
        today = date.today().strftime('%Y-%m-%d')
        conn = get_db_connection()
        
        if request.method == 'POST':
            data_scarico = request.form.get('data', today)
            codice_mp = request.form.get('materiale_codice')
            mp_search = request.form.get('mp_search')
            lotto_interno = request.form.get('lotto_interno')
            quantita_str = request.form.get('quantita', '0')
            causale = request.form.get('causale')
            operatore = request.form.get('operatore')
            data_ultimo_utilizzo = request.form.get('data_ultimo_utilizzo')
            
            form_data = {
                'data': data_scarico,
                'materiale_codice': codice_mp,
                'mp_search': mp_search,
                'lotto_interno': lotto_interno,
                'quantita': quantita_str,
                'causale': causale,
                'operatore': operatore,
                'data_ultimo_utilizzo': data_ultimo_utilizzo
            }

            try:
                quantita = float(quantita_str) if quantita_str else 0.0
            except ValueError:
                quantita = 0.0
            
            if not (codice_mp and lotto_interno and quantita > 0 and operatore):
                flash('Errore: Compila tutti i campi obbligatori (Materiale, Lotto, Quantità > 0, Operatore)!')
                materie = conn.execute('SELECT codice, nome_mp FROM Elenco_MP ORDER BY nome_mp ASC').fetchall()
                conn.close()
                return render_template('scarico_manuale.html', materie=materie, today=today, form_data=form_data)
            else:
                try:
                    lotto_row = conn.execute("SELECT * FROM Lotti_Interni WHERE lotto_interno = ?", (lotto_interno,)).fetchone()
                    if not lotto_row:
                        flash("Errore: Lotto non trovato.")
                        materie = conn.execute('SELECT codice, nome_mp FROM Elenco_MP ORDER BY nome_mp ASC').fetchall()
                        return render_template('scarico_manuale.html', materie=materie, today=today, form_data=form_data)
                    else:
                        try:
                            current_giacenza = float(lotto_row['giacenza']) if lotto_row['giacenza'] else 0.0
                        except ValueError:
                            current_giacenza = 0.0
                        
                        if quantita > current_giacenza:
                            flash(f"Errore: Quantità insufficiente nel lotto! Disponibile: {current_giacenza}, Richiesto: {quantita}")
                            materie = conn.execute('SELECT codice, nome_mp FROM Elenco_MP ORDER BY nome_mp ASC').fetchall()
                            return render_template('scarico_manuale.html', materie=materie, today=today, form_data=form_data)

                        new_giacenza = current_giacenza - quantita
                        
                        conn.execute("UPDATE Lotti_Interni SET giacenza = ? WHERE lotto_interno = ?", (str(new_giacenza), lotto_interno))
                        
                        if causale and causale.strip().lower() == 'controcampione':
                            conn.execute("UPDATE Lotti_Interni SET cc = 'OK' WHERE lotto_interno = ?", (lotto_interno,))
                        
                        conn.execute("""
                            INSERT INTO Scarichi (data, lotto_interno, causale, quantita, operatore, materiale_codice, data_ultimo_utilizzo)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (data_scarico, lotto_interno, causale, quantita, operatore, codice_mp, data_ultimo_utilizzo))
                        
                        new_scarico_val = {
                            'data': data_scarico,
                            'lotto_interno': lotto_interno,
                            'causale': causale,
                            'quantita': quantita,
                            'operatore': operatore,
                            'materiale_codice': codice_mp,
                            'data_ultimo_utilizzo': data_ultimo_utilizzo,
                            'nuova_giacenza_lotto': new_giacenza
                        }
                        
                        log_audit(
                            azione="SCARICO_MANUALE",
                            tabella_interessata="Scarichi",
                            operatore=operatore,
                            vecchio_valore=dict(lotto_row) if lotto_row else None,
                            nuovo_valore=new_scarico_val,
                            conn=conn
                        )
                        
                        conn.commit()
                        flash(f'Scarico registrato con successo! Nuova giacenza: {new_giacenza}')
                        return redirect(url_for('storico_scarichi'))
                except Exception as e:
                    flash(f'Errore durante la registrazione: {e}')
                    materie = conn.execute('SELECT codice, nome_mp FROM Elenco_MP ORDER BY nome_mp ASC').fetchall()
                    return render_template('scarico_manuale.html', materie=materie, today=today, form_data=form_data)
                finally:
                    conn.close()
        
        materie = conn.execute('SELECT codice, nome_mp FROM Elenco_MP ORDER BY nome_mp ASC').fetchall()
        conn.close()
        return render_template('scarico_manuale.html', materie=materie, today=today)

    @app.route('/api/lotti_disponibili/<codice_mp>')
    def api_lotti_disponibili(codice_mp):
        conn = get_db_connection()
        lotti_rows = conn.execute('''
            SELECT lotto_interno, giacenza, lotto_fornitore, data_scadenza
            FROM Lotti_Interni 
            WHERE codice_mp = ? 
              AND (chiuso IS NULL OR chiuso != "SI" AND chiuso != "X")
            ORDER BY data_scadenza ASC, data_arrivo ASC
        ''', (codice_mp,)).fetchall()
        
        lotti = []
        for row in lotti_rows:
            try:
                val = row['giacenza']
                if val is None or str(val).strip() == "":
                    g = 0.0
                else:
                    g = float(val)
                
                if g > 0:
                    lotti.append(dict(row))
            except (ValueError, TypeError):
                pass
                
        conn.close()
        return {'lotti': lotti}

    @app.route('/storico_scarichi')
    def storico_scarichi():
        conn = get_db_connection()
        scarichi_rows = conn.execute('''
            SELECT S.*, M.nome_mp, L.data_scadenza
            FROM Scarichi S
            LEFT JOIN Elenco_MP M ON S.materiale_codice = M.codice
            LEFT JOIN Lotti_Interni L ON S.lotto_interno = L.lotto_interno
            ORDER BY S.data DESC, S.id DESC
        ''').fetchall()
        
        grouped_list = []
        fdg_groups = {}
        
        for row in scarichi_rows:
            r = dict(row)
            if r['lotto_prod']:
                key = (r['data'], r['lotto_prod'])
                if key not in fdg_groups:
                    fdg_groups[key] = {
                        'id': f"fdg_{r['lotto_prod']}_{r['data'].replace('-', '')}",
                        'data': r['data'],
                        'operatore': r['operatore'],
                        'lotto_prod': r['lotto_prod'],
                        'causale': r['causale'],
                        'tipologia': 'Picking FDG',
                        'materiale_nome': f"Produzione {r['lotto_prod']}",
                        'dettagli': []
                    }
                fdg_groups[key]['dettagli'].append(r)
                if r['materiale_codice'] in ('4599', '4600', '4601', '5694', '4602'):
                    fdg_groups[key]['tipologia'] = 'Picking FDG TRASIS'
                elif r['materiale_codice'] in ('5734', '5736', '5735', '5780', '5177'):
                    fdg_groups[key]['tipologia'] = 'Picking FBB TRASIS'
                elif r['materiale_codice'] in ('5612', '5611', '5614', '5613', '2073', '4486', '5686', '5659', '5679', '3136', '2691', '5584'):
                    fdg_groups[key]['tipologia'] = 'Picking FET'
                elif r['materiale_codice'] in ('4482', '4483', '4484', '4523', '4487', '4485', '3945', '4491', '4622'):
                    fdg_groups[key]['tipologia'] = 'Picking DOTA'
                elif r['materiale_codice'] in ('5365', '5366', '5368', '5367', '5585', '63'):
                    fdg_groups[key]['tipologia'] = 'Picking PYL'
                elif r['materiale_codice'] in ('5653', '5652', '5651'):
                    fdg_groups[key]['tipologia'] = 'Picking FCH'
                elif r['materiale_codice'] in ('4663',):
                    fdg_groups[key]['tipologia'] = 'Picking FMC KIT ACC'
                elif r['materiale_codice'] in ('2266', '2267', '2070', '2263', '2264', '2265', '2046', '2262', '2273', '2381', '2071', '3209'):
                    fdg_groups[key]['tipologia'] = 'Picking FMC'
                elif r['materiale_codice'] in ('2730', '2731', '2812', '4636'):
                    fdg_groups[key]['tipologia'] = 'Picking FBB'
            else:
                grouped_list.append({
                    'id': f"man_{r['id']}",
                    'data': r['data'],
                    'operatore': r['operatore'],
                    'lotto_prod': None,
                    'causale': r['causale'],
                    'tipologia': 'Manuale',
                    'materiale_nome': r['nome_mp'],
                    'dettagli': [r]
                })
                
        for group in fdg_groups.values():
            grouped_list.append(group)
            
        grouped_list.sort(key=lambda x: x['data'], reverse=True)
        
        conn.close()
        return render_template('storico_scarichi.html', scarichi=grouped_list)

    @app.route('/scarico_automatico')
    def scarico_automatico():
        return render_template('scarico_automatico.html')

    def get_materie_con_lotti(materie_list):
        conn = get_db_connection()
        for item in materie_list:
            lotti_rows = conn.execute('''
                SELECT lotto_interno, giacenza, data_scadenza
                FROM Lotti_Interni 
                WHERE codice_mp = ? 
                  AND (chiuso IS NULL OR chiuso != "SI" AND chiuso != "X")
                  AND CAST(giacenza AS FLOAT) > 0
                ORDER BY data_scadenza ASC, data_arrivo ASC
            ''', (item['codice'],)).fetchall()
            item['lotti'] = [dict(row) for row in lotti_rows]
        conn.close()
        return {'materie': materie_list}

    @app.route('/api/materie_fmc_kit_acc')
    def api_materie_fmc_kit_acc():
        return get_materie_con_lotti([
            {'codice': '2266', 'nome': 'Colina cassetta Synthera per distillazione', 'qnt': 1},
            {'codice': '2267', 'nome': 'Colina cassetta Synthera per alchinazione', 'qnt': 1},
            {'codice': '2070', 'nome': 'Resin cartridge Se (QMA colina)', 'qnt': 1},
            {'codice': '2263', 'nome': 'Cartucce Silica', 'qnt': 3},
            {'codice': '2264', 'nome': 'HLB cartucce', 'qnt': 1},
            {'codice': '2265', 'nome': 'Acell Plus CM (Colina)', 'qnt': 1},
            {'codice': '2046', 'nome': 'Cryptand Solution', 'qnt': 1},
            {'codice': '4663', 'nome': 'Kit accessori colina', 'qnt': 1},
            {'codice': '2273', 'nome': 'DMAE', 'qnt': 2},
            {'codice': '2073', 'nome': 'Etanolo', 'qnt': 10},
            {'codice': '2072', 'nome': 'Acetonitrile', 'qnt': 3},
            {'codice': '2071', 'nome': 'Dibromomethane', 'qnt': 1},
            {'codice': '3209', 'nome': 'Ammoniaca (colina)', 'qnt': 1},
            {'codice': '3099', 'nome': 'Vial da 10 ml', 'qnt': 2},
            {'codice': '3094', 'nome': 'Vial da 4,5 ml', 'qnt': 1},
            {'codice': '3096', 'nome': 'Vial da 4 ml', 'qnt': 1},
            {'codice': '3095', 'nome': 'Setti da 13 mm', 'qnt': 1},
            {'codice': '3097', 'nome': 'Setti da 11 mm', 'qnt': 1},
            {'codice': '461', 'nome': 'Kit di frazionamento', 'qnt': 1},
            {'codice': '701', 'nome': 'Sodio cloruro 0,9% (250 ml)', 'qnt': 1},
            {'codice': '4379', 'nome': 'Flaconi sterili apirogeni crimpati HUAYI', 'qnt': 10},
            {'codice': '4380', 'nome': 'Capsule sterili HUAYI', 'qnt': 10},
            {'codice': '2395', 'nome': 'Filtri STERIFIX', 'qnt': 1},
            {'codice': '1368', 'nome': 'Filtro Millex OR 0.22 micron', 'qnt': 1},
            {'codice': '605', 'nome': 'Piastre TSA 55 mm', 'qnt': 8},
            {'codice': '606', 'nome': 'Piastre TSA 90 mm', 'qnt': 6},
            {'codice': '424', 'nome': 'Acqua arricchita [18O]H2O', 'qnt': 8.1}
        ])

    @app.route('/api/materie_fmc')
    def api_materie_fmc():
        return get_materie_con_lotti([
            {'codice': '2266', 'nome': 'Colina cassetta Synthera per distillazione', 'qnt': 1},
            {'codice': '2267', 'nome': 'Colina cassetta Synthera per alchinazione', 'qnt': 1},
            {'codice': '2070', 'nome': 'Resin cartridge Se (QMA colina)', 'qnt': 1},
            {'codice': '2263', 'nome': 'Cartucce Silica', 'qnt': 3},
            {'codice': '2264', 'nome': 'HLB cartucce', 'qnt': 1},
            {'codice': '2265', 'nome': 'Acell Plus CM (Colina)', 'qnt': 1},
            {'codice': '2046', 'nome': 'Cryptand Solution', 'qnt': 1},
            {'codice': '2262', 'nome': 'Acido Cloridrico', 'qnt': 10},
            {'codice': '2273', 'nome': 'DMAE', 'qnt': 2},
            {'codice': '2073', 'nome': 'Etanolo', 'qnt': 10},
            {'codice': '2072', 'nome': 'Acetonitrile', 'qnt': 3},
            {'codice': '2381', 'nome': 'Sodio Idrogeno Carbonato', 'qnt': 1},
            {'codice': '2071', 'nome': 'Dibromomethane', 'qnt': 1},
            {'codice': '3209', 'nome': 'Ammoniaca (colina)', 'qnt': 1},
            {'codice': '3099', 'nome': 'Vial da 10 ml', 'qnt': 2},
            {'codice': '3094', 'nome': 'Vial da 4,5 ml', 'qnt': 1},
            {'codice': '3096', 'nome': 'Vial da 4 ml', 'qnt': 1},
            {'codice': '3095', 'nome': 'Setti da 13 mm', 'qnt': 3},
            {'codice': '3097', 'nome': 'Setti da 11 mm', 'qnt': 1},
            {'codice': '461', 'nome': 'Kit di frazionamento', 'qnt': 1},
            {'codice': '701', 'nome': 'Sodio cloruro 0,9% (250 ml)', 'qnt': 1},
            {'codice': '4379', 'nome': 'Flaconi sterili apirogeni crimpati HUAYI', 'qnt': 20},
            {'codice': '4380', 'nome': 'Capsule sterili HUAYI', 'qnt': 20},
            {'codice': '2395', 'nome': 'Filtri STERIFIX', 'qnt': 1},
            {'codice': '1368', 'nome': 'Filtro Millex OR 0.22 micron', 'qnt': 1},
            {'codice': '605', 'nome': 'Piastre TSA 55 mm', 'qnt': 8},
            {'codice': '606', 'nome': 'Piastre TSA 90 mm', 'qnt': 6},
            {'codice': '424', 'nome': 'Acqua arricchita [18O]H2O', 'qnt': 7.6}
        ])

    @app.route('/api/materie_fch')
    def api_materie_fch():
        return get_materie_con_lotti([
            {'codice': '5653', 'nome': 'Fcholine Trasis cassette', 'qnt': 1},
            {'codice': '5652', 'nome': 'Fcholine Trasis Kit of reagents', 'qnt': 1},
            {'codice': '5651', 'nome': 'Fcholine Trasis KIT eluent QMA (2-8°C)', 'qnt': 1},
            {'codice': '5659', 'nome': 'Sodio Cloruro 0,9% Bag 250ml', 'qnt': 1},
            {'codice': '4487', 'nome': 'Acqua PPI Bag 250ml', 'qnt': 1},
            {'codice': '2691', 'nome': 'Filtro Millex GP', 'qnt': 1},
            {'codice': '5584', 'nome': 'Filtro Pall', 'qnt': 1},
            {'codice': '461', 'nome': 'Kit di frazionamento', 'qnt': 1},
            {'codice': '701', 'nome': 'Sodio cloruro 0,9% (250 ml)', 'qnt': 1},
            {'codice': '4379', 'nome': 'Flaconi sterili apirogeni crimpati HUAYI', 'qnt': 10},
            {'codice': '4380', 'nome': 'Capsule sterili HUAYI', 'qnt': 10},
            {'codice': '605', 'nome': 'Piastre TSA 55 mm', 'qnt': 5},
            {'codice': '606', 'nome': 'Piastre TSA 90 mm', 'qnt': 4},
            {'codice': '424', 'nome': 'Acqua arricchita [18O]H2O', 'qnt': 3.8}
        ])

    @app.route('/api/materie_pyl')
    def api_materie_pyl():
        return get_materie_con_lotti([
            {'codice': '5365', 'nome': 'Kit hardware PYL', 'qnt': 1},
            {'codice': '5366', 'nome': 'Kit regenti PYL', 'qnt': 1},
            {'codice': '5368', 'nome': 'Precursore PYL', 'qnt': 1},
            {'codice': '5367', 'nome': 'QMA Eluent PYL', 'qnt': 1},
            {'codice': '5585', 'nome': 'Acetonitrile HPLC', 'qnt': 250},
            {'codice': '2073', 'nome': 'Etanolo', 'qnt': 250},
            {'codice': '4487', 'nome': 'Acqua PPI Bag 250ml', 'qnt': 1},
            {'codice': '63', 'nome': 'Acqua PPI 500ml', 'qnt': 2},
            {'codice': '5584', 'nome': 'Filtro Pall', 'qnt': 1},
            {'codice': '1368', 'nome': 'Filtro Millex OR 0.22 micron', 'qnt': 1},
            {'codice': '461', 'nome': 'Kit di frazionamento', 'qnt': 1},
            {'codice': '701', 'nome': 'Sodio cloruro 0,9% (250 ml)', 'qnt': 1},
            {'codice': '4379', 'nome': 'Flaconi sterili apirogeni crimpati HUAYI', 'qnt': 20},
            {'codice': '4380', 'nome': 'Capsule sterili HUAYI', 'qnt': 20},
            {'codice': '605', 'nome': 'Piastre TSA 55 mm', 'qnt': 8},
            {'codice': '606', 'nome': 'Piastre TSA 90 mm', 'qnt': 6},
            {'codice': '424', 'nome': 'Acqua arricchita [18O]H2O', 'qnt': 8.1}
        ])

    @app.route('/api/materie_dota')
    def api_materie_dota():
        return get_materie_con_lotti([
            {'codice': '4482', 'nome': 'DOPA Trasis Cassette', 'qnt': 1},
            {'codice': '4483', 'nome': 'DOPA Trasis Kit 1 (2-8°C)', 'qnt': 1},
            {'codice': '4484', 'nome': 'DOPA Trasis Kit 2', 'qnt': 1},
            {'codice': '4486', 'nome': 'Acqua PPI Bottiglia 1L', 'qnt': 1},
            {'codice': '4523', 'nome': 'Acqua PPI Bottiglia 250ml', 'qnt': 2},
            {'codice': '4487', 'nome': 'Acqua PPI Bag 250ml', 'qnt': 1},
            {'codice': '2073', 'nome': 'Etanolo', 'qnt': 250},
            {'codice': '4485', 'nome': 'Acido ascorbico', 'qnt': 1},
            {'codice': '3945', 'nome': 'Acido acetico', 'qnt': 2},
            {'codice': '4491', 'nome': 'Sodio acetato triidrato', 'qnt': 3.81},
            {'codice': '461', 'nome': 'Kit di frazionamento', 'qnt': 1},
            {'codice': '4622', 'nome': 'Vials 100ml sterile', 'qnt': 1},
            {'codice': '2074', 'nome': 'Filtro Millex GS Vented', 'qnt': 3},
            {'codice': '1368', 'nome': 'Filtro Millex OR 0.22 micron', 'qnt': 1},
            {'codice': '4379', 'nome': 'Flaconi sterili apirogeni crimpati HUAYI', 'qnt': 10},
            {'codice': '4380', 'nome': 'Capsule sterili HUAYI', 'qnt': 10},
            {'codice': '605', 'nome': 'Piastre TSA 55 mm', 'qnt': 8},
            {'codice': '606', 'nome': 'Piastre TSA 90 mm', 'qnt': 6},
            {'codice': '424', 'nome': 'Acqua arricchita [18O]H2O', 'qnt': 4.0}
        ])

    @app.route('/api/materie_fet')
    def api_materie_fet():
        return get_materie_con_lotti([
            {'codice': '5612', 'nome': 'Kit Hardware FET', 'qnt': 1},
            {'codice': '5611', 'nome': 'Kit reagenti FET', 'qnt': 1},
            {'codice': '5614', 'nome': 'Precursore FET', 'qnt': 1},
            {'codice': '5613', 'nome': 'QMA Eluent FET (2-8°C)', 'qnt': 1},
            {'codice': '2073', 'nome': 'Etanolo', 'qnt': 250},
            {'codice': '4486', 'nome': 'Acqua PPI Bottiglia 1L', 'qnt': 1},
            {'codice': '5686', 'nome': 'Sodio Cloruro 0,9% Bottiglia 250ml', 'qnt': 2},
            {'codice': '5659', 'nome': 'Sodio Cloruro 0,9% Bag 250ml', 'qnt': 1},
            {'codice': '5679', 'nome': 'Strip Acido Ascorbico', 'qnt': 2},
            {'codice': '3136', 'nome': 'Sodio Ascorbato', 'qnt': 1.0},
            {'codice': '461', 'nome': 'Kit di frazionamento', 'qnt': 1},
            {'codice': '701', 'nome': 'Sodio cloruro 0,9% (250 ml)', 'qnt': 1},
            {'codice': '2691', 'nome': 'Filtro Millex GP', 'qnt': 1},
            {'codice': '5584', 'nome': 'Filtro Pall', 'qnt': 1},
            {'codice': '4379', 'nome': 'Flaconi sterili apirogeni crimpati HUAYI', 'qnt': 10},
            {'codice': '4380', 'nome': 'Capsule sterili HUAYI', 'qnt': 10},
            {'codice': '605', 'nome': 'Piastre TSA 55 mm', 'qnt': 0},
            {'codice': '606', 'nome': 'Piastre TSA 90 mm', 'qnt': 0},
            {'codice': '424', 'nome': 'Acqua arricchita [18O]H2O', 'qnt': 4.1}
        ])

    @app.route('/api/materie_fbb_trasis')
    def api_materie_fbb_trasis():
        return get_materie_con_lotti([
            {'codice': '5734', 'nome': 'Kit hardware AIO FBB', 'qnt': 1},
            {'codice': '5736', 'nome': 'Kit reagenti 1/2 (15-25°C) AIO FBB', 'qnt': 1},
            {'codice': '5735', 'nome': 'Kit reagenti 2/2 (2-8°C) AIO FBB', 'qnt': 1},
            {'codice': '2730', 'nome': 'Kit purificazione FBB', 'qnt': 1},
            {'codice': '461', 'nome': 'Kit di frazionamento', 'qnt': 1},
            {'codice': '5780', 'nome': 'Filtro Cathivex-GV', 'qnt': 1},
            {'codice': '5177', 'nome': 'Filtro Millex GV', 'qnt': 1},
            {'codice': '4379', 'nome': 'Flaconi sterili apirogeni crimpati HUAYI', 'qnt': 10},
            {'codice': '4380', 'nome': 'Capsule sterili HUAYI', 'qnt': 10},
            {'codice': '605', 'nome': 'Piastre TSA 55 mm', 'qnt': 5},
            {'codice': '606', 'nome': 'Piastre TSA 90 mm', 'qnt': 4},
            {'codice': '424', 'nome': 'Acqua arricchita [18O]H2O', 'qnt': 8.1}
        ])

    @app.route('/api/materie_fbb')
    def api_materie_fbb():
        return get_materie_con_lotti([
            {'codice': '741', 'nome': 'Kit IFP Synthera', 'qnt': 1},
            {'codice': '2730', 'nome': 'Kit purificazione FBB', 'qnt': 1},
            {'codice': '2731', 'nome': 'Kit reagenti FBB', 'qnt': 1},
            {'codice': '2812', 'nome': 'Kit reagenti FBB (2-8°C)', 'qnt': 1},
            {'codice': '461', 'nome': 'Kit di frazionamento', 'qnt': 1},
            {'codice': '4636', 'nome': 'Filtro Minisart 0,22 micron', 'qnt': 2},
            {'codice': '4379', 'nome': 'Flaconi sterili apirogeni crimpati HUAYI', 'qnt': 20},
            {'codice': '4380', 'nome': 'Capsule sterili HUAYI', 'qnt': 20},
            {'codice': '605', 'nome': 'Piastre TSA 55 mm', 'qnt': 5},
            {'codice': '606', 'nome': 'Piastre TSA 90 mm', 'qnt': 4},
            {'codice': '424', 'nome': 'Acqua arricchita [18O]H2O', 'qnt': 4.1}
        ])

    @app.route('/api/materie_trasis')
    def api_materie_trasis():
        return get_materie_con_lotti([
            {'codice': '4599', 'nome': 'Kit Hardware FDG TRASIS', 'qnt': 1},
            {'codice': '4600', 'nome': 'Kit reagenti FDG TRASIS', 'qnt': 1},
            {'codice': '4601', 'nome': 'Mannosio Triflato TRASIS', 'qnt': 1},
            {'codice': '5694', 'nome': 'Chromabond FDG TRASIS', 'qnt': 1},
            {'codice': '4602', 'nome': 'Acqua PPI Bag 1L', 'qnt': 1},
            {'codice': '461', 'nome': 'Kit di frazionamento', 'qnt': 1},
            {'codice': '701', 'nome': 'Sodio cloruro 0,9% (250 ml)', 'qnt': 1},
            {'codice': '4379', 'nome': 'Flaconi sterili apirogeni crimpati HUAYI', 'qnt': 20},
            {'codice': '4380', 'nome': 'Capsule sterili HUAYI', 'qnt': 20},
            {'codice': '1368', 'nome': 'Filtro Millex OR 0.22 micron', 'qnt': 1},
            {'codice': '2074', 'nome': 'Filtro Millex GS Vented', 'qnt': 1},
            {'codice': '521', 'nome': 'Sodio Cloruro 10%', 'qnt': 1},
            {'codice': '4357', 'nome': 'Etanolo eccipiente', 'qnt': 1},
            {'codice': '605', 'nome': 'Piastre TSA 55 mm', 'qnt': 8},
            {'codice': '606', 'nome': 'Piastre TSA 90 mm', 'qnt': 6},
            {'codice': '424', 'nome': 'Acqua arricchita [18O]H2O', 'qnt': 8.1}
        ])

    @app.route('/api/materie_fdg')
    def api_materie_fdg():
        return get_materie_con_lotti([
            {'codice': '741', 'nome': 'Kit IFP Synthera', 'qnt': 1},
            {'codice': '2065', 'nome': 'Kit chimico reagenti Synthera', 'qnt': 1},
            {'codice': '742', 'nome': 'Mannosio Triflato Synthera', 'qnt': 1},
            {'codice': '740', 'nome': 'Kit accessori Synthera', 'qnt': 1},
            {'codice': '461', 'nome': 'Kit di frazionamento', 'qnt': 1},
            {'codice': '1368', 'nome': 'Filtro Millex OR 0.22 micron', 'qnt': 2},
            {'codice': '701', 'nome': 'Sodio cloruro 0,9% (250 ml)', 'qnt': 1},
            {'codice': '4379', 'nome': 'Flaconi sterili apirogeni crimpati HUAYI', 'qnt': 20},
            {'codice': '4380', 'nome': 'Capsule sterili HUAYI', 'qnt': 20},
            {'codice': '605', 'nome': 'Piastre TSA 55 mm', 'qnt': 5},
            {'codice': '606', 'nome': 'Piastre TSA 90 mm', 'qnt': 4},
            {'codice': '521', 'nome': 'Sodio Cloruro 10%', 'qnt': 1},
            {'codice': '3600', 'nome': 'Kit aggiuntivo di frazionamento', 'qnt': 1},
            {'codice': '4357', 'nome': 'Etanolo eccipiente', 'qnt': 1},
            {'codice': '424', 'nome': 'Acqua arricchita [18O]H2O', 'qnt': 4.1}
        ])

    @app.route('/scarico_fdg', methods=['POST'])
    def scarico_fdg():
        today = date.today().strftime('%Y-%m-%d')
        
        data_json = request.get_json()
        if not data_json:
            return {'success': False, 'message': 'Dati mancanti'}, 400
        
        lotto_prod = data_json.get('lotto_prod')
        operatore = data_json.get('operatore')
        data_scarico = data_json.get('data', today)
        items = data_json.get('items', [])
        
        if not (lotto_prod and operatore and items):
            return {'success': False, 'message': 'Campi obbligatori mancanti (Lotto Prod, Operatore, Items)'}, 400
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            for item in items:
                codice = item['codice_mp']
                lotto = item['lotto_interno']
                
                try:
                    quantita_str = str(item['quantita']).replace(',', '.')
                    quantita = float(quantita_str)
                except (ValueError, TypeError):
                    return {'success': False, 'message': f'La quantità "{item.get("quantita")}" per l\'articolo con codice {codice} non è un numero valido.'}, 400
                    
                if quantita <= 0:
                    return {'success': False, 'message': f'La quantità per l\'articolo con codice {codice} deve essere maggiore di zero.'}, 400
                
                row = cursor.execute('''
                    SELECT L.giacenza, M.nome_mp 
                    FROM Lotti_Interni L 
                    JOIN Elenco_MP M ON L.codice_mp = M.codice 
                    WHERE L.lotto_interno = ?
                ''', (lotto,)).fetchone()
                
                if not row:
                    return {'success': False, 'message': f'Lotto {lotto} non trovato'}, 400
                
                giacenza = float(row['giacenza']) if row['giacenza'] else 0.0
                if quantita > giacenza:
                    nome_mp = row['nome_mp'] or codice
                    return {'success': False, 'message': f'Giacenza insufficiente per {nome_mp} (Lotto {lotto}). Disponibile: {giacenza}, Richiesta: {quantita}'}, 400
            
            for item in items:
                codice = item['codice_mp']
                lotto = item['lotto_interno']
                quantita = float(str(item['quantita']).replace(',', '.'))
                
                lotto_row = cursor.execute("SELECT * FROM Lotti_Interni WHERE lotto_interno = ?", (lotto,)).fetchone()
                old_giacenza = float(lotto_row['giacenza']) if lotto_row and lotto_row['giacenza'] is not None else 0.0
                new_giacenza = old_giacenza - quantita
                
                cursor.execute("UPDATE Lotti_Interni SET giacenza = giacenza - ? WHERE lotto_interno = ?", (quantita, lotto))
                
                cursor.execute("""
                    INSERT INTO Scarichi (data, lotto_interno, causale, quantita, operatore, materiale_codice, lotto_prod)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (data_scarico, lotto, 'Produzione', quantita, operatore, codice, lotto_prod))
                
                new_scarico_val = {
                    'data': data_scarico,
                    'lotto_interno': lotto,
                    'causale': 'Produzione',
                    'quantita': quantita,
                    'operatore': operatore,
                    'materiale_codice': codice,
                    'lotto_prod': lotto_prod,
                    'nuova_giacenza_lotto': new_giacenza
                }
                
                log_audit(
                    azione="SCARICO_AUTOMATICO",
                    tabella_interessata="Scarichi",
                    operatore=operatore,
                    vecchio_valore=dict(lotto_row) if lotto_row else None,
                    nuovo_valore=new_scarico_val,
                    conn=conn
                )
            
            conn.commit()
            return {'success': True, 'message': 'Scarico FDG completato con successo!'}
        
        except Exception as e:
            conn.rollback()
            return {'success': False, 'message': f'Errore durante lo scarico: {str(e)}'}, 500
        finally:
            conn.close()

    @app.route('/api/save_picking_pdf', methods=['POST'])
    def save_picking_pdf():
        try:
            data = request.get_json()
            group_id = data.get('group_id')
            batch = data.get('batch', 'N/A')
            data_scarico = data.get('date', 'N/A')
            operatore = data.get('operatore', 'N/A')
            items = data.get('items', [])

            # Directory di salvataggio
            save_dir = PICKING_LIST_DIR
            if not os.path.isabs(save_dir):
                save_dir = os.path.join(app.root_path, save_dir)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            filename = f"Picking_{batch}_{data_scarico.replace('-', '')}_{datetime.now().strftime('%H%M%S')}.pdf"
            filepath = os.path.join(save_dir, filename)

            # Generazione PDF
            genera_pdf_picking(batch, data_scarico, operatore, items, filepath)

            return jsonify({'success': True, 'path': filepath})

        except Exception as e:
            app.logger.error(f"Error saving PDF: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/api/scarichi_per_lotto/<lotto_interno>')
    def api_scarichi_per_lotto(lotto_interno):
        conn = get_db_connection()
        try:
            rows = conn.execute('''
                SELECT data, causale, lotto_prod, quantita, operatore
                FROM Scarichi
                WHERE lotto_interno = ?
                ORDER BY data DESC, id DESC
            ''', (lotto_interno,)).fetchall()
            
            scarichi = [dict(row) for row in rows]
            return {'success': True, 'scarichi': scarichi}
        except Exception as e:
            return {'success': False, 'message': str(e)}, 500
        finally:
            conn.close()
