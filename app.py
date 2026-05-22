from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
import json
from datetime import datetime, timedelta
from fpdf import FPDF
from dotenv import load_dotenv

# Carica le variabili di ambiente dal file .env se presente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "materie_prime_secret")

# Configurazione Database e Directory di Backup
DB_PATH = os.getenv("DB_PATH", os.path.join("database", "database.db"))
BACKUP_DIR = os.getenv("BACKUP_DIR", os.path.join("database", "backups"))

# Configurazione Cartelle per i Documenti PDF Generati
LISTA_DISTRIBUZIONE_DIR = os.getenv("LISTA_DISTRIBUZIONE_DIR", "lista_distribuzione")
RICHIESTA_ANALISI_DIR = os.getenv("RICHIESTA_ANALISI_DIR", "richiesta_analisi")
PICKING_LIST_DIR = os.getenv("PICKING_LIST_DIR", "picking list")

# Configurazione Percorso Log di Sistema
APP_LOG_PATH = os.getenv("APP_LOG_PATH", os.path.join("database", "app.log"))

# Risolve i percorsi in modo relativo alla radice del progetto se non assoluti
def resolve_project_path(path):
    if not os.path.isabs(path):
        return os.path.join(app.root_path, path)
    return path

resolved_db_path = resolve_project_path(DB_PATH)
resolved_backup_dir = resolve_project_path(BACKUP_DIR)
resolved_log_path = resolve_project_path(APP_LOG_PATH)

# Assicura che le cartelle del database e dei log esistano
os.makedirs(os.path.dirname(resolved_db_path), exist_ok=True)
os.makedirs(os.path.dirname(resolved_log_path), exist_ok=True)

# Configura il logger con RotatingFileHandler
import logging
from logging.handlers import RotatingFileHandler

log_handler = RotatingFileHandler(
    resolved_log_path, 
    maxBytes=5*1024*1024, # 5 MegaBytes
    backupCount=5,
    encoding='utf-8'
)
log_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
log_handler.setLevel(logging.INFO)

# Associa sia al logger di Flask che a quello radice
app.logger.addHandler(log_handler)
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)

# Logga l'avvio solo sul processo principale per evitare duplicati in modalità debug
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    app.logger.info("======================================================================")
    app.logger.info(f"🧪 Gestore-Lab: Avvio dell'applicazione Flask")
    app.logger.info(f"💾 Database attivo: {resolved_db_path}")
    app.logger.info(f"🔄 Cartella backups: {resolved_backup_dir}")
    app.logger.info(f"📋 File di log: {resolved_log_path}")
    app.logger.info("======================================================================")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_audit_db():
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Audit_Trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_ora TEXT NOT NULL,
                operatore TEXT,
                azione TEXT NOT NULL,
                tabella_interessata TEXT NOT NULL,
                vecchio_valore TEXT,
                nuovo_valore TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        print(f"Errore durante la creazione della tabella Audit_Trail: {e}")
    finally:
        conn.close()

# Inizializza il database dell'audit trail all'avvio
init_audit_db()

def init_etichette_db():
    conn = get_db_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS Storico_Etichette (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_ora TEXT NOT NULL,
                lotto_interno TEXT NOT NULL,
                codice_mp TEXT NOT NULL,
                nome_mp TEXT NOT NULL,
                data_arrivo TEXT NOT NULL,
                quantita TEXT NOT NULL,
                tipo_stampa TEXT NOT NULL,
                operatore TEXT
            )
        ''')
        conn.commit()
    except Exception as e:
        print(f"Errore durante la creazione della tabella Storico_Etichette: {e}")
    finally:
        conn.close()

# Inizializza il database dello storico etichette all'avvio
init_etichette_db()

def log_audit(azione, tabella_interessata, operatore, vecchio_valore=None, nuovo_valore=None, conn=None):
    data_ora = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    
    vecchio_val_str = json.dumps(vecchio_valore) if isinstance(vecchio_valore, (dict, list)) else vecchio_valore
    nuovo_val_str = json.dumps(nuovo_valore) if isinstance(nuovo_valore, (dict, list)) else nuovo_valore
    
    if not operatore or not str(operatore).strip():
        operatore = "Sistema"
        
    local_conn = False
    if conn is None:
        conn = get_db_connection()
        local_conn = True
        
    try:
        conn.execute('''
            INSERT INTO Audit_Trail (data_ora, operatore, azione, tabella_interessata, vecchio_valore, nuovo_valore)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data_ora, operatore, azione, tabella_interessata, vecchio_val_str, nuovo_val_str))
        if local_conn:
            conn.commit()
    except Exception as e:
        print(f"Errore durante l'inserimento dell'audit trail: {e}")
    finally:
        if local_conn:
            conn.close()

@app.template_filter('dateformat')
def dateformat_filter(value, format='%d-%m-%Y'):
    if not value or value == '-':
        return value
    try:
        # Tenta di convertire da YYYY-MM-DD a DD-MM-YYYY
        dt = datetime.strptime(value, '%Y-%m-%d')
        return dt.strftime(format)
    except:
        return value

@app.template_filter('format_date')
def format_date_filter(value):
    if not value:
        return ""
    try:
        # Se è già in formato DD-MM-YYYY lo restituiamo
        if len(value) == 10 and value[2] == '-' and value[5] == '-':
            return value
        return datetime.strptime(value, '%Y-%m-%d').strftime('%d-%m-%p').replace('-PM', '-').replace('-AM', '-') # Fix per alcuni sistemi, ma usiamo quello standard:
    except:
        try:
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
            # Arrotonda giacenza a 2 decimali per pulizia
            item['giacenza_totale'] = round(item['giacenza_totale'], 2)
            sotto_scorta.append(item)
            
    conn.close()
    
    return render_template('index.html', 
                           lotti_scaduti=lotti_scaduti, 
                           lotti_in_scadenza=lotti_in_scadenza, 
                           sotto_scorta=sotto_scorta)

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
                
                log_audit(
                    azione="INSERIMENTO",
                    tabella_interessata="Elenco_MP",
                    operatore="Sistema",
                    nuovo_valore=data,
                    conn=conn
                )
                
                conn.commit()
                flash('Prodotto aggiunto con successo!')
                return redirect(url_for('product_list'))
            except sqlite3.IntegrityError:
                flash(f'Errore: Il codice {data["codice"]} esiste già nel database!')
                return render_template('add_product.html', form_data=data)
            finally:
                conn.close()

    return render_template('add_product.html')

@app.route('/update_product', methods=['POST'])
def update_product():
    conn = get_db_connection()
    original_codice = request.form['original_codice']
    codice = request.form['codice']
    nome_mp = request.form['nome_mp']
    nome_file = request.form['nome_file']
    nome_etichetta = request.form['nome_etichetta']
    unita_misura = request.form['unita_misura']
    codice_fornitore = request.form['codice_fornitore']
    uso = request.form['uso']
    controcampione = request.form['controcampione']
    distribuzione = request.form['distribuzione']
    scorta_minima = request.form.get('scorta_minima') or 0

    try:
        # Recupera il vecchio valore prima della modifica
        old_row = conn.execute("SELECT * FROM Elenco_MP WHERE codice = ?", (original_codice,)).fetchone()
        old_val = dict(old_row) if old_row else None

        # Se il codice cambia, aggiorniamo in cascata le tabelle collegate
        if codice != original_codice:
            conn.execute('UPDATE Lotti_Interni SET codice_mp = ? WHERE codice_mp = ?', (codice, original_codice))
            conn.execute('UPDATE Scarichi SET materiale_codice = ? WHERE materiale_codice = ?', (codice, original_codice))
            
        conn.execute('''UPDATE Elenco_MP SET 
                        codice = ?, nome_mp = ?, nome_file = ?, nome_etichetta = ?, unita_misura = ?, 
                        codice_fornitore = ?, uso = ?, controcampione = ?, distribuzione = ?, scorta_minima = ?
                        WHERE codice = ?''',
                     (codice, nome_mp, nome_file, nome_etichetta, unita_misura, 
                      codice_fornitore, uso, controcampione, distribuzione, scorta_minima, original_codice))
        
        new_val = {
            'codice': codice,
            'nome_mp': nome_mp,
            'nome_file': nome_file,
            'nome_etichetta': nome_etichetta,
            'unita_misura': unita_misura,
            'codice_fornitore': codice_fornitore,
            'uso': uso,
            'controcampione': controcampione,
            'distribuzione': distribuzione,
            'scorta_minima': scorta_minima
        }
        
        log_audit(
            azione="MODIFICA",
            tabella_interessata="Elenco_MP",
            operatore="Sistema",
            vecchio_valore=old_val,
            nuovo_valore=new_val,
            conn=conn
        )
        
        conn.commit()
        flash('Materia prima aggiornata con successo!', 'success')
    except sqlite3.IntegrityError:
        flash(f'Errore: Il codice {codice} esiste già nel database!', 'error')
    except Exception as e:
        flash(f'Errore durante l\'aggiornamento: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('product_list'))

@app.route('/delete_product', methods=['POST'])
def delete_product():
    conn = get_db_connection()
    codice = request.form['codice']
    try:
        # Recupera il vecchio valore prima dell'eliminazione
        old_row = conn.execute("SELECT * FROM Elenco_MP WHERE codice = ?", (codice,)).fetchone()
        old_val = dict(old_row) if old_row else None

        # Eliminiamo in cascata lotti e scarichi collegati per pulizia database
        conn.execute('DELETE FROM Lotti_Interni WHERE codice_mp = ?', (codice,))
        conn.execute('DELETE FROM Scarichi WHERE materiale_codice = ?', (codice,))
        conn.execute('DELETE FROM Elenco_MP WHERE codice = ?', (codice,))
        
        log_audit(
            azione="ELIMINAZIONE",
            tabella_interessata="Elenco_MP",
            operatore="Sistema",
            vecchio_valore=old_val,
            nuovo_valore=None,
            conn=conn
        )
        
        conn.commit()
        flash('Materia prima ed eventuali dati associati eliminati con successo!', 'success')
    except Exception as e:
        flash(f'Errore durante l\'eliminazione: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('product_list'))


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
        # Recupera il vecchio valore prima della modifica
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
    from datetime import date
    today = date.today().strftime('%d-%m-%Y')
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
    # Query che aggrega i lotti per ogni materia prima ed estrae il lotto in uso (il più vecchio attivo)
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
    
    # Trova il lotto in uso (quello attivo più vecchio con giacenza > 0)
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
                
    # Aggiungi il flag in_uso a ciascun lotto
    for lot in lotti:
        lot['in_uso'] = (lot['lotto_interno'] == oldest_active_lotto_interno) if oldest_active_lotto_interno else False
        
    conn.close()
    return {'lotti': lotti}

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
        # Recupera il vecchio valore prima dell'approvazione
        old_row = conn.execute("SELECT * FROM Lotti_Interni WHERE lotto_interno = ?", (lotto_interno,)).fetchone()
        old_val = dict(old_row) if old_row else None

        conn.execute('''
            UPDATE Lotti_Interni 
            SET data_approvazione = ?, appr = 'OK' 
            WHERE lotto_interno = ?
        ''', (data_approvazione, lotto_interno))
        
        # Costruisce il nuovo valore
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

def clean_pdf_string(s):
    if not s:
        return ""
    # Sostituzioni comuni per caratteri accentati in italiano
    replacements = {
        'à': "a'", 'á': "a'",
        'è': "e'", 'é': "e'",
        'ì': "i'", 'í': "i'",
        'ò': "o'", 'ó': "o'",
        'ù': "u'", 'ú': "u'",
        'À': "A'", 'È': "E'",
        'Ì': "I'", 'Ò': "O'",
        'Ù': "U'"
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    # Rimpiazza tutti gli altri caratteri non latin-1 con ?
    return s.encode('latin-1', 'replace').decode('latin-1')

@app.route('/api/genera_pdf_distribuzione/<lotto_interno>', methods=['POST'])
def genera_pdf_distribuzione(lotto_interno):
    conn = get_db_connection()
    try:
        # 1. Recupera i dettagli del lotto e della materia prima associata
        lotto_row = conn.execute('''
            SELECT L.*, M.nome_mp 
            FROM Lotti_Interni L 
            LEFT JOIN Elenco_MP M ON L.codice_mp = M.codice 
            WHERE L.lotto_interno = ?
        ''', (lotto_interno,)).fetchone()
        
        if not lotto_row:
            return {'success': False, 'message': 'Lotto non trovato'}, 404
            
        lotto_row = dict(lotto_row)
        
        # 2. Recupera l'elenco degli scarichi per questo lotto in ordine cronologico
        scarichi_rows = conn.execute('''
            SELECT S.data, S.causale, S.quantita, S.operatore, S.lotto_prod, S.data_ultimo_utilizzo 
            FROM Scarichi S
            WHERE S.lotto_interno = ?
            ORDER BY S.data ASC, S.id ASC
        ''', (lotto_interno,)).fetchall()
        
        scarichi = [dict(row) for row in scarichi_rows]
        
        # 3. Creazione cartella di destinazione
        save_dir = LISTA_DISTRIBUZIONE_DIR
        if not os.path.isabs(save_dir):
            save_dir = os.path.join(app.root_path, save_dir)
        os.makedirs(save_dir, exist_ok=True)
        
        # 4. Nome file sanificato
        import re
        safe_lotto = re.sub(r'[\\/*?:"<>|]', '_', lotto_interno)
        filename = f"lista_distribuzione_{safe_lotto}.pdf"
        filepath = os.path.join(save_dir, filename)
        
        # 5. Generazione del PDF con FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=10)
        
        # Header Box (Bordo principale)
        pdf.rect(10, 10, 190, 25)
        
        # Logo aziendale (se presente)
        logo_path = os.path.join("static", "img", "logo.jpg")
        if os.path.exists(logo_path):
            pdf.image(logo_path, 15, 12, 35)
            
        pdf.line(55, 10, 55, 35)
        
        # Titolo
        pdf.set_font("helvetica", "B", 12)
        pdf.set_xy(55, 10)
        pdf.cell(95, 25, "LISTA DI DISTRIBUZIONE LOTTO", border=0, align="C")
        
        pdf.line(150, 10, 150, 35)
        
        # Data di generazione e Pagina
        pdf.set_font("helvetica", size=8)
        pdf.set_xy(150, 10)
        pdf.cell(50, 12.5, f"Data: {datetime.now().strftime('%d-%m-%Y')}", border="B", align="C")
        pdf.set_xy(150, 22.5)
        pdf.cell(50, 12.5, "Pagina: 1 di 1", align="C")
        
        # Meta informazioni sul lotto e la materia prima
        pdf.ln(15)
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(190, 8, clean_pdf_string("DETTAGLIO MATERIA PRIMA E LOTTO"), ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
        
        nome_materia = lotto_row.get('nome_mp') or "N.D."
        codice_materia = lotto_row.get('codice_mp') or "N.D."
        lotto_forn = lotto_row.get('lotto_fornitore') or "N.D."
        forn = lotto_row.get('fornitore') or "N.D."
        scadenza = lotto_row.get('data_scadenza') or "N.D."
        arrivo = lotto_row.get('data_arrivo') or "N.D."
        
        # Formattazione date per visualizzazione
        try:
            scad_display = datetime.strptime(scadenza, '%Y-%m-%d').strftime('%d-%m-%Y')
        except:
            scad_display = scadenza
            
        try:
            arrivo_display = datetime.strptime(arrivo, '%Y-%m-%d').strftime('%d-%m-%Y')
        except:
            arrivo_display = arrivo
            
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(35, 6, "Materia Prima:")
        pdf.set_font("helvetica", size=9)
        pdf.cell(155, 6, clean_pdf_string(f"{nome_materia} (Codice: {codice_materia})"), ln=True)
        
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(35, 6, "Lotto Interno:")
        pdf.set_font("helvetica", size=9)
        pdf.cell(60, 6, clean_pdf_string(lotto_interno))
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(35, 6, "Lotto Fornitore:")
        pdf.set_font("helvetica", size=9)
        pdf.cell(60, 6, clean_pdf_string(lotto_forn), ln=True)
        
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(35, 6, "Fornitore:")
        pdf.set_font("helvetica", size=9)
        pdf.cell(60, 6, clean_pdf_string(forn))
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(35, 6, "Data Arrivo:")
        pdf.set_font("helvetica", size=9)
        pdf.cell(60, 6, clean_pdf_string(arrivo_display), ln=True)
        
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(35, 6, "Data Scadenza:")
        pdf.set_font("helvetica", size=9)
        pdf.cell(60, 6, clean_pdf_string(scad_display))
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(35, 6, "Data Stampa PDF:")
        pdf.set_font("helvetica", size=9)
        pdf.cell(60, 6, datetime.now().strftime('%d-%m-%Y %H:%M:%S'), ln=True)
        
        pdf.ln(6)
        
        # Tabella degli utilizzi (Scarichi)
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(190, 8, clean_pdf_string("REGISTRO DEGLI UTILIZZI (SCARICHI)"), ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        
        try:
            qnt_iniziale = float(lotto_row.get('qnt_arrivata') or 0)
        except (ValueError, TypeError):
            qnt_iniziale = 0.0

        def format_qty(val):
            try:
                val_f = float(val)
                if val_f.is_integer():
                    return str(int(val_f))
                return f"{val_f:.2f}".rstrip('0').rstrip('.')
            except:
                return str(val)

        if not scarichi:
            pdf.set_font("helvetica", "I", 10)
            pdf.cell(190, 8, clean_pdf_string("Nessun utilizzo o scarico registrato per questo lotto."), ln=True)
        else:
            # Larghezze colonne: Data (30), Causale (65), Quantità (25), Qtà Rimanente (35), Operatore (35) = 190
            pdf.set_font("helvetica", "B", 9)
            pdf.cell(30, 7, "Data", border=1, align="C")
            pdf.cell(65, 7, "Causale", border=1, align="C")
            pdf.cell(25, 7, clean_pdf_string("Quantita'"), border=1, align="C")
            pdf.cell(35, 7, clean_pdf_string("Q.ta' Rimanente"), border=1, align="C")
            pdf.cell(35, 7, "Operatore", border=1, align="C", ln=True)
            
            pdf.set_font("helvetica", size=8)
            qnt_rimanente = qnt_iniziale
            for row in scarichi:
                try:
                    data_disp = datetime.strptime(row['data'], '%Y-%m-%d').strftime('%d-%m-%Y')
                except:
                    data_disp = row['data'] or "-"
                    
                try:
                    q_scarico = float(row['quantita'] or 0)
                except:
                    q_scarico = 0.0
                    
                qnt_rimanente -= q_scarico
                
                pdf.cell(30, 6, clean_pdf_string(data_disp), border=1, align="C")
                pdf.cell(65, 6, clean_pdf_string(row['causale']), border=1)
                pdf.cell(25, 6, clean_pdf_string(format_qty(q_scarico)), border=1, align="C")
                pdf.cell(35, 6, clean_pdf_string(format_qty(qnt_rimanente)), border=1, align="C")
                pdf.cell(35, 6, clean_pdf_string(row['operatore']), border=1, ln=True)
                
        # 6. Salvataggio del PDF
        pdf.output(filepath)
        
        return {'success': True, 'filename': filename, 'path': filepath}
        
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500
    finally:
        conn.close()

@app.route('/api/aggiungi_attesa_qc/<lotto_interno>', methods=['POST'])
def api_aggiungi_attesa_qc(lotto_interno):
    conn = get_db_connection()
    try:
        # Recupera il vecchio valore per l'audit trail
        old_row = conn.execute("SELECT * FROM Lotti_Interni WHERE lotto_interno = ?", (lotto_interno,)).fetchone()
        if not old_row:
            return {'success': False, 'message': 'Lotto non trovato'}, 404
        old_val = dict(old_row)

        conn.execute("UPDATE Lotti_Interni SET qc_attesa = 'SI' WHERE lotto_interno = ?", (lotto_interno,))
        
        # Costruisce il nuovo valore
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
        # Recupera il vecchio valore per l'audit trail
        old_row = conn.execute("SELECT * FROM Lotti_Interni WHERE lotto_interno = ?", (lotto_interno,)).fetchone()
        if not old_row:
            return {'success': False, 'message': 'Lotto non trovato'}, 404
        old_val = dict(old_row)

        conn.execute("UPDATE Lotti_Interni SET qc_attesa = 'NO' WHERE lotto_interno = ?", (lotto_interno,))
        
        # Costruisce il nuovo valore
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

@app.route('/api/stampa_richiesta_analisi', methods=['POST'])
def api_stampa_richiesta_analisi():
    conn = get_db_connection()
    try:
        # 1. Recupera tutti i lotti in attesa di QC
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
        
        # 2. Creazione cartella di destinazione
        save_dir = RICHIESTA_ANALISI_DIR
        if not os.path.isabs(save_dir):
            save_dir = os.path.join(app.root_path, save_dir)
        os.makedirs(save_dir, exist_ok=True)
        
        # 3. Nome file basato sulla data e ora odierna (YYYYMMDD_HHMMSS) per evitare sovrascritture
        today_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"richiesta_analisi_{today_str}.pdf"
        filepath = os.path.join(save_dir, filename)
        
        # 4. Generazione del PDF con FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(10, 10, 10)
        pdf.set_auto_page_break(auto=True, margin=10)
        
        # --- DISEGNO INTESTAZIONE (EXCEL STYLE GRID) ---
        # Disegnamo la struttura superiore (tabella 190mm di larghezza)
        # Bordo esterno principale dell'intestazione
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.3)
        
        # Top-left cell: Logo
        # Width 55, Height 22
        pdf.rect(10, 10, 55, 22)
        logo_path = os.path.join("static", "img", "logo.jpg")
        if os.path.exists(logo_path):
            pdf.image(logo_path, 15, 12.5, 45)
        else:
            pdf.set_font("helvetica", "B", 18)
            pdf.set_text_color(79, 70, 229) # Indaco
            pdf.set_xy(10, 10)
            pdf.cell(55, 22, "CURIUM", align="C")
            pdf.set_text_color(0, 0, 0)
            
        # Top-right cell: Title
        # Width 135, Height 22
        pdf.rect(65, 10, 135, 22)
        pdf.set_xy(65, 10)
        pdf.set_font("helvetica", size=9)
        pdf.cell(135, 7, "  Titolo:", align="L")
        
        pdf.set_font("helvetica", "B", 13)
        pdf.set_xy(65, 17)
        pdf.cell(135, 10, "RICHIESTA D'ANALISI", align="C")
        
        # Row 2 (SOP section below logo and title):
        # Column 1 (SOP): width 55, height 12
        pdf.rect(10, 32, 55, 12)
        pdf.set_xy(10, 32)
        pdf.set_font("helvetica", size=8)
        pdf.cell(55, 5, " SOP DI RIFERIMENTO:", ln=True)
        pdf.set_font("helvetica", "B", 9)
        pdf.set_x(10)
        pdf.cell(55, 6, " UDN-PRD-001")
        
        # Column 2 (Revisione): width 40, height 12
        pdf.rect(65, 32, 40, 12)
        pdf.set_xy(65, 32)
        pdf.set_font("helvetica", size=9)
        pdf.cell(40, 12, "Revisione: 11", align="C")
        
        # Column 3 (Pagina): width 95, height 12
        pdf.rect(105, 32, 95, 12)
        pdf.set_xy(105, 32)
        pdf.set_font("helvetica", size=9)
        pdf.cell(95, 12, "Pagina: 1 di 1", align="C")
        
        # --- TESTO INTRODUTTIVO ---
        pdf.set_xy(10, 52)
        pdf.set_font("helvetica", "B", 10.5)
        testo_intro = "Si richiede l'esecuzione dei controlli sui seguenti materiali posti in stato di QUARANTENA"
        pdf.cell(190, 8, clean_pdf_string(testo_intro), align="C")
        
        pdf.ln(12)
        
        # --- TABELLA DATI ---
        # Colonne: Materiale (45), N° lotto interno (25), Nome fornitore (30), N° lotto fornitore (30), Data di arrivo (20), Quantità (20), Data di QC (20)
        # Sum = 190
        widths = [45, 25, 30, 30, 20, 20, 20]
        headers = ["Materiale", "N. lotto interno", "Nome fornitore", "N. lotto fornitore", "Data di arrivo", "Quantita", "Data di QC"]
        
        # Scrittura intestazione tabella
        pdf.set_font("helvetica", "B", 9)
        pdf.set_fill_color(240, 240, 240)
        for w, h_text in zip(widths, headers):
            pdf.cell(w, 10, clean_pdf_string(h_text), border=1, align="C", fill=True)
        pdf.ln()
        
        pdf.set_font("helvetica", size=8.5)
        today_fmt = datetime.now().strftime('%d/%m/%Y')
        for lot in lotti:
            # Formatta la data di arrivo da YYYY-MM-DD a DD/MM/YYYY
            data_arr = lot.get('data_arrivo') or ""
            try:
                dt = datetime.strptime(data_arr, '%Y-%m-%d')
                data_arr_fmt = dt.strftime('%d/%m/%Y')
            except:
                data_arr_fmt = data_arr
                
            qnt_val = lot.get('qnt_arrivata') or ""
            um = lot.get('unita_misura') or ""
            qnt_str = f"{qnt_val} {um}".strip()
            
            # Troncamento per sicurezza layout
            materia_nome = lot.get('nome_mp') or ""
            if len(materia_nome) > 26:
                materia_nome = materia_nome[:23] + "..."
                
            forn_nome = lot.get('fornitore') or ""
            if len(forn_nome) > 17:
                forn_nome = forn_nome[:14] + "..."
                
            lotto_forn_val = lot.get('lotto_fornitore') or ""
            if len(lotto_forn_val) > 18:
                lotto_forn_val = lotto_forn_val[:15] + "..."
            
            # Scrittura dei campi
            pdf.cell(45, 8, clean_pdf_string(materia_nome), border=1)
            pdf.cell(25, 8, clean_pdf_string(lot.get('lotto_interno') or ""), border=1, align="C")
            pdf.cell(30, 8, clean_pdf_string(forn_nome), border=1)
            pdf.cell(30, 8, clean_pdf_string(lotto_forn_val), border=1, align="C")
            pdf.cell(20, 8, clean_pdf_string(data_arr_fmt), border=1, align="C")
            pdf.cell(20, 8, clean_pdf_string(qnt_str), border=1, align="C")
            pdf.cell(20, 8, clean_pdf_string(today_fmt), border=1, align="C")
            pdf.ln()
            
        # Salvataggio PDF
        pdf.output(filepath)
        
        # --- AGGIORNAMENTO STATO LOTTI COINVOLTI & AUDIT ---
        today_iso = datetime.now().strftime('%Y-%m-%d')
        
        for lot in lotti:
            lotto_interno = lot['lotto_interno']
            
            # Recupera il vecchio valore per l'audit
            old_row = conn.execute("SELECT * FROM Lotti_Interni WHERE lotto_interno = ?", (lotto_interno,)).fetchone()
            old_val = dict(old_row) if old_row else None
            
            # Aggiorna
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
                # Retrieve current lotto state
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
                    
                    # Costruisce il nuovo valore dello scarico per l'audit trail
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
            # Rileva se si tratta di un picking TRASIS o FBB o FET o DOTA o PYL o FCH o FMC o FMC_KIT_ACC controllando la presenza di un componente specifico
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

@app.route('/api/materie_fmc_kit_acc')
def api_materie_fmc_kit_acc():
    # Lista completa di materiali per FMC KIT ACC con codici e quantità standard
    materie_fmc_kit_acc = [
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
    ]
    
    conn = get_db_connection()
    for item in materie_fmc_kit_acc:
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
    return {'materie': materie_fmc_kit_acc}

@app.route('/api/materie_fmc')
def api_materie_fmc():
    # Lista completa di materiali per FMC con codici e quantità standard
    materie_fmc = [
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
    ]
    
    conn = get_db_connection()
    for item in materie_fmc:
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
    return {'materie': materie_fmc}

@app.route('/api/materie_fch')
def api_materie_fch():
    # Lista completa di materiali per FCH con codici e quantità standard
    materie_fch = [
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
    ]
    
    conn = get_db_connection()
    for item in materie_fch:
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
    return {'materie': materie_fch}

@app.route('/api/materie_pyl')
def api_materie_pyl():
    # Lista completa di materiali per PYL con codici e quantità standard
    materie_pyl = [
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
    ]
    
    conn = get_db_connection()
    for item in materie_pyl:
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
    return {'materie': materie_pyl}

@app.route('/api/materie_dota')
def api_materie_dota():
    # Lista completa di materiali per DOTA con codici e quantità standard
    materie_dota = [
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
    ]
    
    conn = get_db_connection()
    for item in materie_dota:
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
    return {'materie': materie_dota}

@app.route('/api/materie_fet')
def api_materie_fet():
    # Lista completa di materiali per FET con codici e quantità standard
    materie_fet = [
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
    ]
    
    conn = get_db_connection()
    for item in materie_fet:
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
    return {'materie': materie_fet}

@app.route('/api/materie_fbb_trasis')
def api_materie_fbb_trasis():
    # Lista completa di materiali per FBB TRASIS con codici e quantità standard
    materie_fbb_trasis = [
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
    ]
    
    conn = get_db_connection()
    for item in materie_fbb_trasis:
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
    return {'materie': materie_fbb_trasis}

@app.route('/api/materie_fbb')
def api_materie_fbb():
    # Lista completa di materiali per FBB con codici e quantità standard
    materie_fbb = [
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
    ]
    
    conn = get_db_connection()
    for item in materie_fbb:
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
    return {'materie': materie_fbb}

@app.route('/api/materie_trasis')
def api_materie_trasis():
    # Lista completa di materiali per FDG TRASIS con codici e quantità standard
    materie_trasis = [
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
    ]
    
    conn = get_db_connection()
    for item in materie_trasis:
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
    return {'materie': materie_trasis}

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
            
            try:
                # Support both comma and dot decimal formats
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
        
        # 2. Esecuzione scarichi
        for item in items:
            codice = item['codice_mp']
            lotto = item['lotto_interno']
            quantita = float(str(item['quantita']).replace(',', '.'))
            
            # Recupera il vecchio valore del lotto prima dello scarico
            lotto_row = cursor.execute("SELECT * FROM Lotti_Interni WHERE lotto_interno = ?", (lotto,)).fetchone()
            old_giacenza = float(lotto_row['giacenza']) if lotto_row and lotto_row['giacenza'] is not None else 0.0
            new_giacenza = old_giacenza - quantita
            
            # Aggiorna giacenza
            cursor.execute("UPDATE Lotti_Interni SET giacenza = giacenza - ? WHERE lotto_interno = ?", (quantita, lotto))
            
            # Inserisce record scarico
            cursor.execute("""
                INSERT INTO Scarichi (data, lotto_interno, causale, quantita, operatore, materiale_codice, lotto_prod)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (data_scarico, lotto, 'Produzione', quantita, operatore, codice, lotto_prod))
            
            # Costruisce il nuovo valore dello scarico per l'audit trail
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
        # Formattazione data per il PDF (da YYYY-MM-DD a DD-MM-YYYY)
        try:
            dt_display = datetime.strptime(data_scarico, '%Y-%m-%d').strftime('%d-%m-%Y')
        except:
            dt_display = data_scarico
            
        operatore = data.get('operatore', 'N/A')
        items = data.get('items', [])

        # Directory di salvataggio
        save_dir = PICKING_LIST_DIR
        if not os.path.isabs(save_dir):
            save_dir = os.path.join(app.root_path, save_dir)
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
        pdf.multi_cell(50, 5, f"SOP di riferimento: \nxxx", align="C")
        
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
        pdf.cell(30, 8, dt_display, border=1, new_x="LMARGIN", new_y="NEXT")

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
            # Formatta la scadenza dell'item per il PDF
            try:
                scad_display = datetime.strptime(item['data_scad'], '%Y-%m-%d').strftime('%d-%m-%Y')
            except:
                scad_display = item['data_scad']

            pdf.cell(10, 7, str(item['num']), border=1, align="C")
            pdf.cell(25, 7, str(item['codice']), border=1, align="C")
            pdf.cell(85, 7, str(item['articolo']), border=1)
            pdf.cell(20, 7, str(item['quantita']), border=1, align="C")
            pdf.cell(30, 7, str(item['lotto_n']), border=1, align="C")
            pdf.cell(20, 7, scad_display, border=1, align="C", new_x="LMARGIN", new_y="NEXT")

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
        pdf.cell(63, 10, dt_display, border=1)
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


@app.route('/audit_trail')
def audit_trail():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM Audit_Trail ORDER BY id DESC").fetchall()
        audit_records = [dict(row) for row in rows]
    except Exception as e:
        flash(f"Errore nel recupero dello storico operazioni: {e}", "error")
        audit_records = []
    finally:
        conn.close()
    return render_template('audit_trail.html', audit_records=audit_records)


@app.route('/nuova_etichetta')
def nuova_etichetta():
    conn = get_db_connection()
    try:
        # Recupera tutti i lotti registrati (non chiusi) associandoli ai dettagli della materia prima
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

        # Recupera lo stato delle etichette già stampate per ciascun lotto
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
        print(f"Errore nel recupero dei lotti per le etichette: {e}")
        lotti = []
    finally:
        conn.close()
    
    return render_template('nuova_etichetta.html', lotti=lotti)



@app.route('/storico_etichetta')
def storico_etichetta():
    conn = get_db_connection()
    try:
        # Recupera lo storico delle etichette facendo un LEFT JOIN con Lotti_Interni
        # per ricavare i dettagli supplementari utili ad una ristampa fedele dell'etichetta verde.
        rows = conn.execute('''
            SELECT S.id, S.data_ora, S.lotto_interno, S.codice_mp, S.nome_mp, S.data_arrivo, S.quantita, S.tipo_stampa, S.operatore,
                   L.lotto_fornitore, L.data_scadenza, L.data_approvazione
            FROM Storico_Etichette S
            LEFT JOIN Lotti_Interni L ON S.lotto_interno = L.lotto_interno
            ORDER BY S.id DESC
        ''').fetchall()
        etichette = [dict(row) for row in rows]
    except Exception as e:
        print(f"Errore nel recupero dello storico etichette: {e}")
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
        
        # Prevenzione dei duplicati: verifica se l'etichetta dello stesso tipo per lo stesso lotto è già presente
        existing = conn.execute('''
            SELECT 1 FROM Storico_Etichette 
            WHERE lotto_interno = ? AND tipo_stampa = ?
        ''', (lotto_interno, tipo_stampa)).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'success': False, 'message': 'Un\'etichetta di questo tipo è già stata stampata per questo lotto.'}), 400
            
        # Convalida dei vincoli per la generazione dell'etichetta VERDE
        if tipo_stampa == 'VERDE':
            # 1. L'etichetta BIANCO deve essere già stata generata
            bianca_exists = conn.execute('''
                SELECT 1 FROM Storico_Etichette
                WHERE lotto_interno = ? AND tipo_stampa = 'BIANCO'
            ''', (lotto_interno,)).fetchone()
            if not bianca_exists:
                conn.close()
                return jsonify({'success': False, 'message': "Impossibile stampare l'etichetta verde se l'etichetta bianca non è stata ancora generata."}), 400
                
            # 2. QC impostato e Approvazione su OK
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
        print(f"Errore durante il salvataggio dell'etichetta: {e}")
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


@app.route('/api/spegni', methods=['POST'])
def api_spegni():
    import threading
    import time
    app.logger.warning("Richiesta di spegnimento dell'applicazione Flask ricevuta ed in fase di elaborazione...")
    def kill_server():
        time.sleep(1.0)
        os._exit(0)
    threading.Thread(target=kill_server).start()
    return jsonify({'success': True, 'message': 'Arresto del server in corso... Puoi chiudere questa finestra.'})


@app.route('/settings')
def settings():
    import glob
    import re
    backup_dir = BACKUP_DIR
    if not os.path.exists(backup_dir):
        try:
            os.makedirs(backup_dir)
        except Exception as e:
            app.logger.error(f"Errore creazione cartella backup: {e}", exc_info=True)
        
    backup_files = glob.glob(os.path.join(backup_dir, "*.db"))
    backups_data = []
    
    for filepath in backup_files:
        filename = os.path.basename(filepath)
        try:
            size_bytes = os.path.getsize(filepath)
            size_kb = round(size_bytes / 1024, 2)
        except Exception:
            size_kb = 0.0
        
        # Tipo di backup
        if "emergenza" in filename or "pre_ripristino" in filename:
            tipo = "Emergenza Pre-Ripristino"
        elif "estemporaneo" in filename or "manuale" in filename or "richiesta" in filename:
            tipo = "Estemporaneo da Operatore"
        elif "backup" in filename:
            tipo = "Automatico Programmato"
        else:
            tipo = "Estemporaneo da Operatore"
            
        # Parse timestamp from filename
        match = re.search(r'(\d{8}_\d{6})', filename)
        dt = None
        if match:
            ts_str = match.group(1)
            try:
                dt = datetime.strptime(ts_str, '%Y%m%d_%H%M%S')
            except ValueError:
                pass
        
        if dt is None:
            try:
                mtime = os.path.getmtime(filepath)
                dt = datetime.fromtimestamp(mtime)
            except Exception:
                dt = datetime.now()
            
        formatted_date = dt.strftime('%d-%m-%Y')
        formatted_time = dt.strftime('%H:%M:%S')
        
        backups_data.append({
            'filename': filename,
            'size_kb': size_kb,
            'tipo': tipo,
            'data': formatted_date,
            'ora': formatted_time,
            'datetime_obj': dt
        })
        
    # Ordinamento dal più recente al più vecchio
    backups_data.sort(key=lambda x: x['datetime_obj'], reverse=True)
    
    return render_template('settings.html', backups=backups_data)


@app.route('/settings/backup/create', methods=['POST'])
def settings_backup_create():
    import shutil
    operatore = request.form.get('operatore', '').strip()
    if not operatore:
        flash("Inserire il nome dell'operatore per procedere.", "error")
        return redirect(url_for('settings'))
        
    src_db = DB_PATH
    backup_dir = BACKUP_DIR
    if not os.path.exists(backup_dir):
        try:
            os.makedirs(backup_dir)
        except Exception as e:
            app.logger.error(f"Impossibile creare la cartella di backup: {e}", exc_info=True)
            flash(f"Impossibile creare la cartella di backup: {e}", "error")
            return redirect(url_for('settings'))
        
    if not os.path.exists(src_db):
        app.logger.error(f"Errore creazione backup: file database attivo non trovato a percorso '{src_db}'")
        flash("Errore: database.db attivo non trovato!", "error")
        return redirect(url_for('settings'))
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"database_estemporaneo_{timestamp}.db"
    dst_db = os.path.join(backup_dir, filename)
    
    try:
        shutil.copy2(src_db, dst_db)
        app.logger.info(f"Backup manuale '{filename}' creato con successo dall'operatore '{operatore}'.")
        # Rotazione per mantenere max 30 backup standard
        esegui_rotazione_backups()
        
        # Log nell'audit trail
        log_audit(
            azione="Creazione Backup Manuale", 
            tabella_interessata="Database", 
            operatore=operatore, 
            nuovo_valore=filename
        )
        
        flash(f"Backup manuale creato con successo: {filename}", "success")
    except Exception as e:
        app.logger.error(f"Errore durante la creazione del backup manuale da '{operatore}': {e}", exc_info=True)
        flash(f"Errore durante la creazione del backup: {e}", "error")
        
    return redirect(url_for('settings'))


@app.route('/settings/backup/restore', methods=['POST'])
def settings_backup_restore():
    import shutil
    filename = request.form.get('filename', '').strip()
    conferma = request.form.get('conferma', '').strip()
    operatore = request.form.get('operatore', '').strip()
    
    if not filename:
        flash("Nessun file di backup specificato.", "error")
        return redirect(url_for('settings'))
        
    if conferma != "RIPRISTINA":
        flash("Conferma non valida. Digitare 'RIPRISTINA' per procedere.", "error")
        return redirect(url_for('settings'))
        
    if not operatore:
        flash("Nome dell'operatore richiesto per procedere.", "error")
        return redirect(url_for('settings'))
        
    # Impedisci directory traversal e convalida percorso file
    filename = os.path.basename(filename)
    backup_path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(backup_path):
        app.logger.error(f"Tentato ripristino di file inesistente '{filename}' dall'operatore '{operatore}'")
        flash("Il file di backup selezionato non esiste.", "error")
        return redirect(url_for('settings'))
        
    active_db_path = DB_PATH
    
    # 1. Backup Preventivo Immediato di Emergenza
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    emergenza_filename = f"database_emergenza_pre_ripristino_{timestamp}.db"
    emergenza_path = os.path.join(BACKUP_DIR, emergenza_filename)
    
    try:
        if os.path.exists(active_db_path):
            shutil.copy2(active_db_path, emergenza_path)
            app.logger.warning(f"Inizio ripristino database. Generato backup preventivo di emergenza '{emergenza_filename}'.")
        else:
            app.logger.warning("Attenzione: database attivo non trovato per backup preventivo di emergenza. Procedo.")
    except Exception as e:
        app.logger.error(f"Errore critico nella creazione del backup preventivo di emergenza: {e}", exc_info=True)
        flash(f"Impossibile creare il backup di emergenza preventiva. Operazione annullata. Dettaglio: {e}", "error")
        return redirect(url_for('settings'))
        
    # 2. Ripristino Sicuro tramite SQLite Online Backup API
    conn_src = None
    conn_dst = None
    try:
        conn_src = sqlite3.connect(backup_path)
        conn_dst = sqlite3.connect(active_db_path)
        # Copia atomica a livello di pagine SQLite
        conn_src.backup(conn_dst)
        
        conn_src.close()
        conn_dst.close()
        
        app.logger.warning(f"Ripristino database 'a caldo' eseguito con successo da '{filename}' dall'operatore '{operatore}'.")
        
        # Scrivi log nell'Audit Trail (sul DB appena ripristinato)
        log_audit(
            azione="Ripristino Database 'a Caldo'", 
            tabella_interessata="Database", 
            operatore=operatore, 
            vecchio_valore=f"Ripristinato da file: {filename}",
            nuovo_valore=f"Emergenza generata: {emergenza_filename}"
        )
        
        flash(f"Database ripristinato con successo da '{filename}'! Creato backup di emergenza preventiva '{emergenza_filename}'.", "success")
    except Exception as e:
        app.logger.error(f"Errore critico durante il ripristino 'a caldo' del database da '{filename}': {e}", exc_info=True)
        flash(f"Errore critico durante il ripristino 'a caldo' del database: {e}", "error")
        
    return redirect(url_for('settings'))


@app.route('/settings/backup/download/<filename>')
def settings_backup_download(filename):
    # Prevenzione Directory Traversal
    filename = os.path.basename(filename)
    backup_dir = os.path.abspath(BACKUP_DIR)
    filepath = os.path.join(backup_dir, filename)
    if not os.path.exists(filepath):
        app.logger.error(f"Richiesto download di file inesistente '{filename}'")
        flash("File di backup non trovato.", "error")
        return redirect(url_for('settings'))
        
    from flask import send_from_directory
    app.logger.info(f"Download avviato per il file di backup: {filename}")
    return send_from_directory(backup_dir, filename, as_attachment=True)


@app.route('/settings/logs')
def settings_logs():
    if not os.path.exists(resolved_log_path):
        return jsonify({'success': True, 'logs': 'Nessun log presente.'})
    try:
        with open(resolved_log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            last_lines = lines[-150:]
            return jsonify({'success': True, 'logs': ''.join(last_lines)})
    except Exception as e:
        app.logger.error(f"Errore durante la lettura del file di log: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/settings/logs/download')
def settings_logs_download():
    directory = os.path.dirname(resolved_log_path)
    filename = os.path.basename(resolved_log_path)
    if not os.path.exists(resolved_log_path):
        flash("File di log di sistema non ancora generato.", "error")
        return redirect(url_for('settings'))
    app.logger.info("Download avviato per il file di log di sistema completo app.log")
    from flask import send_from_directory
    return send_from_directory(directory, filename, as_attachment=True)


def esegui_rotazione_backups():
    """
    Mantiene solo gli ultimi 30 file di backup più recenti ordinati per timestamp nel nome file.
    """
    import glob
    try:
        backup_dir = BACKUP_DIR
        if not os.path.exists(backup_dir):
            return
            
        # Trova tutti i backup .db
        backups = glob.glob(os.path.join(backup_dir, "database_backup_*.db"))
        # Ordinamento alfabetico (grazie a YYYYMMDD_HHMMSS equivale a cronologico)
        backups.sort()
        
        # Se superano i 30, eliminiamo quelli in più a partire dal più vecchio
        if len(backups) > 30:
            to_delete = backups[:-30]
            for file_path in to_delete:
                try:
                    os.remove(file_path)
                    app.logger.info(f"Rotazione backup: rimosso vecchio file {file_path}")
                except Exception as ex:
                    app.logger.error(f"Errore durante l'eliminazione del vecchio backup {file_path}: {ex}")
            app.logger.info(f"Rotazione backup eseguita. Rimossi {len(to_delete)} backup in eccesso.")
    except Exception as e:
        app.logger.error(f"Errore critico durante la rotazione dei backup: {e}", exc_info=True)


def ciclo_backup_background():
    """
    Ciclo continuo in background per garantire almeno un backup al giorno.
    Controlla periodicamente (ogni ora) e genera un backup se manca quello per il giorno corrente.
    """
    import shutil
    import glob
    import time
    
    # Ritardo iniziale all'avvio per non rallentare il bootstrap iniziale di Flask
    time.sleep(5)
    
    # Esegui subito una rotazione iniziale per pulire la cartella se piena al boot
    esegui_rotazione_backups()
    
    backup_dir = BACKUP_DIR
    if not os.path.exists(backup_dir):
        try:
            os.makedirs(backup_dir)
        except Exception as e:
            app.logger.error(f"[BACKUP AUTOMATICO] Impossibile creare la cartella di backup: {e}", exc_info=True)
            return

    while True:
        try:
            today_str = datetime.now().strftime('%Y%m%d')
            
            # Cerca se esiste già un backup per oggi
            today_backups = glob.glob(os.path.join(backup_dir, f"database_backup_{today_str}_*.db"))
            if not today_backups:
                src_db = DB_PATH
                if os.path.exists(src_db):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    dst_db = os.path.join(backup_dir, f"database_backup_{timestamp}.db")
                    shutil.copy2(src_db, dst_db)
                    app.logger.info(f"Backup automatico programmato creato con successo: database_backup_{timestamp}.db")
                    
                    # Riapri la rotazione per mantenere solo 30 file
                    esegui_rotazione_backups()
                else:
                    app.logger.warning("[BACKUP AUTOMATICO] Attenzione: file database attivo non trovato!")
        except Exception as e:
            app.logger.error(f"[BACKUP AUTOMATICO] Errore nel ciclo di background: {e}", exc_info=True)
            
        # Attendi un'ora (3600 secondi) prima del controllo successivo
        time.sleep(3600)


def avvia_schedulatore_backup():
    """
    Avvia il thread demone per il backup in background.
    Se Flask è in modalità debug, assicura di avviarsi una sola volta.
    """
    import threading
    # Avvia solo sul processo principale se in modalità debug (Werkzeug reloader)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        t = threading.Thread(target=ciclo_backup_background, daemon=True)
        t.start()
        app.logger.info("Thread di controllo e backup automatico in background avviato con successo.")


# Avvio dello schedulatore all'importazione/inizializzazione del modulo
avvia_schedulatore_backup()


if __name__ == '__main__':
    import socket
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
            
    flask_host = os.getenv("FLASK_HOST", "0.0.0.0")
    flask_port = int(os.getenv("FLASK_PORT", "5000"))
    flask_debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t", "y", "yes")

    local_ip = get_local_ip()
    print("\n" + "="*70)
    print(f"  * SERVER APERTO ALLA RETE LOCALE (LAN) *")
    print(f"  Puoi accedere all'applicazione da smartphone, tablet o altri PC:")
    print(f"  -> http://{local_ip}:{flask_port}")
    print("="*70 + "\n")
    
    app.logger.info(f"Server Web Flask avviato ed in ascolto su http://{local_ip}:{flask_port} (Porta LAN: {flask_port})")
    
    app.run(host=flask_host, port=flask_port, debug=flask_debug)

