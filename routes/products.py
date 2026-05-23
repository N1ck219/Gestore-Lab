import sqlite3
from flask import render_template, request, redirect, url_for, flash
from db_utils import get_db_connection, log_audit

def register_products_routes(app):
    @app.route('/list')
    def product_list():
        query = request.args.get('q')
        conn = get_db_connection()
        if query:
            products_rows = conn.execute("SELECT * FROM Elenco_MP WHERE nome_mp LIKE ? OR codice LIKE ?", 
                                    ('%' + query + '%', '%' + query + '%')).fetchall()
        else:
            products_rows = conn.execute('SELECT * FROM Elenco_MP ORDER BY nome_mp ASC').fetchall()
        
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
            old_row = conn.execute("SELECT * FROM Elenco_MP WHERE codice = ?", (original_codice,)).fetchone()
            old_val = dict(old_row) if old_row else None

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
            old_row = conn.execute("SELECT * FROM Elenco_MP WHERE codice = ?", (codice,)).fetchone()
            old_val = dict(old_row) if old_row else None

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
