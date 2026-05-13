from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "materie_prime_secret"

DB_PATH = os.path.join("database", "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
        codice = request.form['codice']
        nome_mp = request.form['nome_mp']
        nome_file = request.form['nome_file']
        nome_etichetta = request.form['nome_etichetta']
        unita_misura = request.form['unita_misura']
        codice_fornitore = request.form['codice_fornitore']
        uso = request.form['uso']
        controcampione = request.form['controcampione']
        distribuzione = request.form['distribuzione']
        
        # Validazione: tutti obbligatori tranne codice_fornitore
        required_fields = [codice, nome_mp, nome_file, nome_etichetta, unita_misura, uso]
        if not all(required_fields):
            flash('Tutti i campi sono obbligatori (tranne il Codice Fornitore)!')
        else:
            conn = get_db_connection()
            try:
                conn.execute('''INSERT INTO Elenco_MP 
                                (codice, nome_mp, nome_file, nome_etichetta, unita_misura, codice_fornitore, uso, controcampione, distribuzione) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (codice, nome_mp, nome_file, nome_etichetta, unita_misura, codice_fornitore, uso, controcampione, distribuzione))
                conn.commit()
                flash('Prodotto aggiunto con successo!')
                return redirect(url_for('product_list'))
            except sqlite3.IntegrityError:
                flash(f'Errore: Il codice {codice} esiste già nel database!')
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
        # Recupero i soli campi obbligatori dal form
        data = {
            'lotto_interno': request.form['lotto_interno'],
            'codice_mp': request.form['codice_mp'],
            'data_arrivo': request.form['data_arrivo'],
            'lotto_fornitore': request.form['lotto_fornitore'],
            'fornitore': request.form['fornitore'],
            'data_scadenza': request.form['data_scadenza'],
            'qnt_arrivata': request.form['qnt_arrivata'],
            'pz_x_cf': request.form['pz_x_cf'],
            'giacenza': request.form['qnt_arrivata'], # Impostiamo la giacenza iniziale uguale alla quantità
            'in_uso': 'SI'
        }
        
        if not all(data.values()):
            flash('Tutti i campi sono obbligatori!')
        else:
            try:
                conn.execute('''INSERT INTO Lotti_Interni 
                                (lotto_interno, codice_mp, data_arrivo, lotto_fornitore, fornitore, data_scadenza, 
                                 qnt_arrivata, pz_x_cf, giacenza, in_uso) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             list(data.values()))
                conn.commit()
                flash('Lotto aggiunto con successo!')
                return redirect(url_for('lotti_list'))
            except sqlite3.IntegrityError:
                flash(f'Errore: Il lotto {data["lotto_interno"]} esiste già!')
            finally:
                conn.close()
                return redirect(url_for('lotti_list'))

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

if __name__ == '__main__':
    app.run(debug=True)
