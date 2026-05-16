from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = "materie_prime_secret"

DB_PATH = os.path.join("database", "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.template_filter('format_date')
def format_date_filter(value):
    if not value or value == '-':
        return "-"
    try:
        # Tenta di convertire da YYYY-MM-DD a DD-MM-YYYY
        dt = datetime.strptime(str(value), '%Y-%m-%d')
        return dt.strftime('%d-%m-%Y')
    except:
        return value

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list')
def product_list():
    query = request.args.get('q')
    conn = get_db_connection()
    if query:
        products_rows = conn.execute("SELECT * FROM Elenco_MP WHERE nome_mp LIKE ? OR codice LIKE ?", 
                                ('%' + query + '%', '%' + query + '%')).fetchall()
    else:
        products_rows = conn.execute('SELECT * FROM Elenco_MP ORDER BY nome_mp ASC').fetchall()
    
    # Convertiamo i Row in dizionari
    products = [dict(row) for row in products_rows]
    conn.close()
    return render_template('list.html', products=products, search_query=query)

@app.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        data = {
            'codice': request.form['codice'],
            'nome_mp': request.form['nome_mp'],
            'nome_file': request.form['nome_file'],
            'nome_etichetta': request.form['nome_etichetta'],
            'unita_misura': request.form['unita_misura'],
            'codice_fornitore': request.form['codice_fornitore'],
            'uso': request.form['uso'],
            'controcampione': request.form['controcampione'],
            'distribuzione': request.form['distribuzione'],
            'scorta_minima': request.form.get('scorta_minima') or 0
        }
        
        # Validazione: tutti obbligatori tranne codice_fornitore e scorta_minima
        required_fields = [data['codice'], data['nome_mp'], data['nome_file'], data['nome_etichetta'], data['unita_misura'], data['uso']]
        if not all(required_fields):
            flash('Tutti i campi sono obbligatori (tranne il Codice Fornitore)!')
            return render_template('add_product.html', form_data=data)
        else:
            conn = get_db_connection()
            try:
                conn.execute('''INSERT INTO Elenco_MP 
                                (codice, nome_mp, nome_file, nome_etichetta, unita_misura, codice_fornitore, uso, controcampione, distribuzione, scorta_minima) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (data['codice'], data['nome_mp'], data['nome_file'], data['nome_etichetta'], 
                              data['unita_misura'], data['codice_fornitore'], data['uso'], 
                              data['controcampione'], data['distribuzione'], data['scorta_minima']))
                conn.commit()
                flash('Prodotto aggiunto con successo!')
                return redirect(url_for('product_list'))
            except sqlite3.IntegrityError:
                flash(f'Errore: Il codice {data["codice"]} esiste già nel database!')
                return render_template('add_product.html', form_data=data)
            finally:
                conn.close()

    return render_template('add_product.html')

@app.route('/lotti')
def lotti_list():
    conn = get_db_connection()
    # Recuperiamo i lotti con il nome della materia prima associata tramite JOIN
    lotti_rows = conn.execute('''
        SELECT L.*, M.nome_mp 
        FROM Lotti_Interni L 
        LEFT JOIN Elenco_MP M ON L.codice_mp = M.codice 
        ORDER BY L.data_arrivo DESC
    ''').fetchall()
    # Convertiamo i Row in dizionari
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
        conn.commit()
        flash('Lotto aggiornato con successo!')
    except Exception as e:
        flash(f'Errore durante l\'aggiornamento: {e}')
    finally:
        conn.close()
    
    return redirect(url_for('lotti_list'))

@app.route('/add_lotto', methods=('GET', 'POST'))
def add_lotto():
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    conn = get_db_connection()
    materie = conn.execute('SELECT codice, nome_mp FROM Elenco_MP ORDER BY nome_mp ASC').fetchall()
    fornitori = conn.execute('SELECT nome FROM Fornitori ORDER BY nome ASC').fetchall()
    
    if request.method == 'POST':
        # Recupero i campi dal form
        data = {
            'lotto_interno': request.form.get('lotto_interno'),
            'codice_mp': request.form.get('codice_mp'),
            'mp_search': request.form.get('mp_search'), # Per mantenere il testo della ricerca
            'data_arrivo': request.form.get('data_arrivo'),
            'lotto_fornitore': request.form.get('lotto_fornitore'),
            'fornitore': request.form.get('fornitore'),
            'data_scadenza': request.form.get('data_scadenza'),
            'qnt_arrivata': request.form.get('qnt_arrivata'),
            'pz_x_cf': request.form.get('pz_x_cf'),
            'giacenza': request.form.get('qnt_arrivata'),
            'in_uso': 'SI'
        }
        
        # Campi obbligatori per il DB (escludendo mp_search che è solo per la UI)
        required_db_fields = ['lotto_interno', 'codice_mp', 'data_arrivo', 'lotto_fornitore', 'fornitore', 'data_scadenza', 'qnt_arrivata', 'pz_x_cf']
        
        if not all(data[f] for f in required_db_fields):
            flash('Tutti i campi sono obbligatori!')
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
                conn.commit()
                flash('Lotto aggiunto con successo!')
                return redirect(url_for('lotti_list'))
            except sqlite3.IntegrityError:
                flash(f'Errore: Il lotto {data["lotto_interno"]} esiste già nel database!')
                return render_template('add_lotto.html', materie=materie, fornitori=fornitori, today=today, form_data=data)
            finally:
                conn.close()
                # Rimosso il redirect forzato dal finally

    conn.close()
    return render_template('add_lotto.html', materie=materie, fornitori=fornitori, today=today)

@app.route('/add_fornitore', methods=['POST'])
def add_fornitore():
    nome = request.form.get('nome', '').strip()
    if not nome:
        return {'success': False, 'message': 'Nome mancante'}, 400
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO Fornitori (nome) VALUES (?)', (nome,))
        conn.commit()
        return {'success': True, 'nome': nome}
    except sqlite3.IntegrityError:
        return {'success': False, 'message': 'Fornitore già esistente'}, 400
    finally:
        conn.close()

# Rimossa rotta search separata, ora integrata in /list

@app.route('/magazzino')
def magazzino():
    conn = get_db_connection()
    # Query che aggrega i lotti per ogni materia prima
    inventory_rows = conn.execute('''
        SELECT 
            M.codice, 
            M.nome_mp, 
            M.scorta_minima,
            M.ordine_magazzino,
            M.categoria_magazzino,
            SUM(CASE WHEN L.giacenza IS NOT NULL THEN CAST(L.giacenza AS FLOAT) ELSE 0 END) as giacenza_totale,
            COUNT(CASE WHEN L.lotto_interno IS NOT NULL THEN 1 END) as num_lotti,
            MIN(CASE WHEN L.data_scadenza != "" THEN L.data_scadenza END) as prossima_scadenza
        FROM Elenco_MP M
        LEFT JOIN Lotti_Interni L ON M.codice = L.codice_mp
        GROUP BY M.codice, M.nome_mp, M.scorta_minima, M.ordine_magazzino, M.categoria_magazzino
        ORDER BY M.ordine_magazzino ASC, M.nome_mp ASC
    ''').fetchall()
    
    inventory = [dict(row) for row in inventory_rows]
    
    # Raggruppiamo per categoria per gestire meglio i divisori sticky nel template
    grouped_inventory = {}
    for item in inventory:
        cat = item['categoria_magazzino'] or 'Altre Materie Prime'
        if cat not in grouped_inventory:
            grouped_inventory[cat] = []
        grouped_inventory[cat].append(item)
        
    conn.close()
    return render_template('magazzino.html', grouped_inventory=grouped_inventory)

@app.route('/api/lotti_per_mp/<codice>')
def api_lotti_per_mp(codice):
    conn = get_db_connection()
    lotti_rows = conn.execute('''
        SELECT 
            arrivo_magazzino, 
            lotto_interno, 
            lotto_fornitore, 
            qnt_arrivata, 
            data_scadenza
        FROM Lotti_Interni 
        WHERE codice_mp = ? 
        ORDER BY data_arrivo DESC
    ''', (codice,)).fetchall()
    
    lotti = [dict(row) for row in lotti_rows]
    conn.close()
    return {'lotti': lotti}

@app.route('/scarico_manuale', methods=['GET', 'POST'])
def scarico_manuale():
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Retrieve form data
        data_scarico = request.form.get('data', today)
        codice_mp = request.form.get('materiale_codice')
        mp_search = request.form.get('mp_search')
        lotto_interno = request.form.get('lotto_interno')
        quantita_str = request.form.get('quantita', '0')
        causale = request.form.get('causale')
        operatore = request.form.get('operatore')
        data_ultimo_utilizzo = request.form.get('data_ultimo_utilizzo')
        
        # Prepare data for persistence
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
                # Retrieve current giacenza
                lotto_row = conn.execute("SELECT giacenza FROM Lotti_Interni WHERE lotto_interno = ?", (lotto_interno,)).fetchone()
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
                    
                    # Update giacenza
                    conn.execute("UPDATE Lotti_Interni SET giacenza = ? WHERE lotto_interno = ?", (str(new_giacenza), lotto_interno))
                    
                    # Automazione Controcampione: se la causale è "Controcampione", segna CC come OK nella tabella Lotti_Interni
                    if causale and causale.strip().lower() == 'controcampione':
                        conn.execute("UPDATE Lotti_Interni SET cc = 'OK' WHERE lotto_interno = ?", (lotto_interno,))
                    
                    # Insert record into Scarichi (removed lotto_prod and controcampione_lotto)
                    conn.execute("""
                        INSERT INTO Scarichi (data, lotto_interno, causale, quantita, operatore, materiale_codice, data_ultimo_utilizzo)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (data_scarico, lotto_interno, causale, quantita, operatore, codice_mp, data_ultimo_utilizzo))
                    
                    conn.commit()
                    flash(f'Scarico registrato con successo! Nuova giacenza: {new_giacenza}')
                    return redirect(url_for('storico_scarichi'))
            except Exception as e:
                flash(f'Errore durante la registrazione: {e}')
                materie = conn.execute('SELECT codice, nome_mp FROM Elenco_MP ORDER BY nome_mp ASC').fetchall()
                return render_template('scarico_manuale.html', materie=materie, today=today, form_data=form_data)
            finally:
                conn.close()
    
    # Per GET
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
    
    # Filter lots that actually have > 0 giacenza
    lotti = []
    for row in lotti_rows:
        try:
            # Handle potential None or empty strings
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
    
    # Raggruppamento per evento
    grouped_list = []
    fdg_groups = {}
    
    for row in scarichi_rows:
        r = dict(row)
        if r['lotto_prod']:
            # Chiave per FDG: (data, lotto_prod)
            # Nota: usiamo anche l'operatore se vogliamo essere sicuri, ma lotto_prod è di solito univoco per quel giorno
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
        else:
            # Scarico manuale - un evento per ogni record
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
            
    # Aggiungi i gruppi FDG
    for group in fdg_groups.values():
        grouped_list.append(group)
        
    # Ordina per data decrescente
    grouped_list.sort(key=lambda x: x['data'], reverse=True)
    
    conn.close()
    return render_template('storico_scarichi.html', scarichi=grouped_list)

@app.route('/scarico_automatico')
def scarico_automatico():
    return render_template('scarico_automatico.html')

@app.route('/api/materie_fdg')
def api_materie_fdg():
    # Lista completa di materiali per FDG con codici e quantità standard
    materie_fdg = [
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
    ]
    
    conn = get_db_connection()
    for item in materie_fdg:
        # Recupera i lotti disponibili per ogni materia
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
    return {'materie': materie_fdg}

@app.route('/scarico_fdg', methods=['POST'])
def scarico_fdg():
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    
    data_json = request.get_json()
    if not data_json:
        return {'success': False, 'message': 'Dati mancanti'}, 400
    
    lotto_prod = data_json.get('lotto_prod')
    operatore = data_json.get('operatore')
    data_scarico = data_json.get('data', today)
    items = data_json.get('items', []) # Lista di {codice_mp, lotto_interno, quantita}
    
    if not (lotto_prod and operatore and items):
        return {'success': False, 'message': 'Campi obbligatori mancanti (Lotto Prod, Operatore, Items)'}, 400
    
    conn = get_db_connection()
    try:
        # Inizia transazione
        cursor = conn.cursor()
        
        # 1. Validazione preliminare di tutti gli stock
        for item in items:
            codice = item['codice_mp']
            lotto = item['lotto_interno']
            quantita = float(item['quantita'])
            
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
                return {'success': False, 'message': f'Giacenza insufficiente per {nome_mp} (Lotto {lotto}). Disponibile: {giacenza}'}, 400
        
        # 2. Esecuzione scarichi
        for item in items:
            codice = item['codice_mp']
            lotto = item['lotto_interno']
            quantita = float(item['quantita'])
            
            # Aggiorna giacenza
            cursor.execute("UPDATE Lotti_Interni SET giacenza = giacenza - ? WHERE lotto_interno = ?", (quantita, lotto))
            
            # Inserisce record scarico
            cursor.execute("""
                INSERT INTO Scarichi (data, lotto_interno, causale, quantita, operatore, materiale_codice, lotto_prod)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (data_scarico, lotto, 'Produzione', quantita, operatore, codice, lotto_prod))
        
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
        raw_date = data.get('date', 'N/A')
        operatore = data.get('operatore', 'N/A')
        items = data.get('items', [])
        
        # Formattazione data per PDF (da YYYY-MM-DD a DD-MM-YYYY)
        try:
            dt_obj = datetime.strptime(raw_date, '%Y-%m-%d')
            data_scarico = dt_obj.strftime('%d-%m-%Y')
        except:
            data_scarico = raw_date

        # Directory di salvataggio
        save_dir = r"D:\python\Gestore-Lab\picking list"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # Nome file unico
        filename = f"Picking_{batch}_{data_scarico.replace('-', '')}_{datetime.now().strftime('%H%M%S')}.pdf"
        filepath = os.path.join(save_dir, filename)

        # Creazione PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=10)

        # Header Box (Main Border)
        pdf.rect(10, 10, 190, 30)
        
        # Left Section (Logo + SOP)
        pdf.line(60, 10, 60, 40)
        logo_path = os.path.join("static", "img", "logo.jpg")
        if os.path.exists(logo_path):
            # Logo centrato nel riquadro superiore (60x20 circa)
            pdf.image(logo_path, 15, 12, 40)
        
        pdf.line(10, 30, 60, 30) # Linea sotto logo
        pdf.set_font("helvetica", size=7)
        pdf.set_xy(10, 30)
        pdf.multi_cell(50, 5, "SOP di riferimento: \nxxx", align="C")
        
        # Middle Section (Allegato + Title)
        pdf.line(150, 10, 150, 40)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_xy(60, 10)
        pdf.cell(90, 15, "ALLEGATO N° 6", border="B", align="C")
        pdf.set_xy(60, 25)
        pdf.cell(90, 15, "PICKING LIST", align="C")
        
        # Right Section (Revision + Page)
        pdf.set_font("helvetica", size=8)
        pdf.set_xy(150, 10)
        pdf.cell(50, 15, "Revisione: 11", border="B", align="L", new_x="RIGHT", new_y="TOP")
        pdf.set_xy(150, 25)
        pdf.cell(50, 15, "Pagina: 1 di 1", align="L")

        # Meta Data
        pdf.set_font("helvetica", size=10)
        pdf.ln(15)
        pdf.set_x(130)
        pdf.cell(40, 8, "Batch Production Nr.:", border=1)
        pdf.cell(30, 8, batch, border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(130)
        pdf.cell(40, 8, "Date:", border=1)
        pdf.cell(30, 8, data_scarico, border=1, new_x="LMARGIN", new_y="NEXT")

        # Table
        pdf.ln(10)
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(10, 8, "Num", border=1, align="C")
        pdf.cell(25, 8, "Codice", border=1, align="C")
        pdf.cell(85, 8, "Articolo", border=1, align="C")
        pdf.cell(20, 8, "Quantita", border=1, align="C")
        pdf.cell(30, 8, "Lotto n.", border=1, align="C")
        pdf.cell(20, 8, "Data scad.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("helvetica", size=8)
        for item in items:
            pdf.cell(10, 7, str(item['num']), border=1, align="C")
            pdf.cell(25, 7, str(item['codice']), border=1, align="C")
            pdf.cell(85, 7, str(item['articolo']), border=1)
            pdf.cell(20, 7, str(item['quantita']), border=1, align="C")
            pdf.cell(30, 7, str(item['lotto_n']), border=1, align="C")
            pdf.cell(20, 7, str(item['data_scad']), border=1, align="C", new_x="LMARGIN", new_y="NEXT")

        # Footer
        pdf.ln(10)
        pdf.set_font("helvetica", "B", 8)
        pdf.cell(0, 5, "Note:", new_x="LMARGIN", new_y="NEXT")
        pdf.rect(10, pdf.get_y(), 190, 20)
        pdf.ln(22)

        pdf.cell(63, 5, "Operatore", border=1)
        pdf.cell(63, 5, "Data", border=1)
        pdf.cell(64, 5, "Firma", border=1, new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(63, 10, operatore, border=1)
        pdf.cell(63, 10, data_scarico, border=1)
        pdf.cell(64, 10, "", border=1, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(5)
        pdf.set_font("helvetica", size=8)
        pdf.cell(95, 8, "Copia n°: ________", new_x="RIGHT", new_y="TOP")
        pdf.cell(95, 8, "Sigla QA su ORIGINALE: ________________", align="R", new_x="LMARGIN", new_y="NEXT")

        pdf.output(filepath)

        return jsonify({'success': True, 'path': filepath})

    except Exception as e:
        print(f"Error saving PDF: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
