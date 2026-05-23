import os
import glob
import re
import shutil
import sqlite3
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from db_utils import get_db_connection, log_audit
from backup_utils import esegui_rotazione_backups
from config import DB_PATH, BACKUP_DIR, RESOLVED_LOG_PATH

def register_settings_routes(app):
    @app.route('/settings')
    def settings():
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
            
            if "emergenza" in filename or "pre_ripristino" in filename:
                tipo = "Emergenza Pre-Ripristino"
            elif "estemporaneo" in filename or "manuale" in filename or "richiesta" in filename:
                tipo = "Estemporaneo da Operatore"
            elif "backup" in filename:
                tipo = "Automatico Programmato"
            else:
                tipo = "Estemporaneo da Operatore"
                
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
            
        backups_data.sort(key=lambda x: x['datetime_obj'], reverse=True)
        return render_template('settings.html', backups=backups_data)

    @app.route('/settings/backup/create', methods=['POST'])
    def settings_backup_create():
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
            esegui_rotazione_backups()
            
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
            conn_src.backup(conn_dst)
            
            conn_src.close()
            conn_dst.close()
            
            app.logger.warning(f"Ripristino database 'a caldo' eseguito con successo da '{filename}' dall'operatore '{operatore}'.")
            
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
        filename = os.path.basename(filename)
        backup_dir = os.path.abspath(BACKUP_DIR)
        filepath = os.path.join(backup_dir, filename)
        if not os.path.exists(filepath):
            app.logger.error(f"Richiesto download di file inesistente '{filename}'")
            flash("File di backup non trovato.", "error")
            return redirect(url_for('settings'))
            
        app.logger.info(f"Download avviato per il file di backup: {filename}")
        return send_from_directory(backup_dir, filename, as_attachment=True)

    @app.route('/settings/logs')
    def settings_logs():
        if not os.path.exists(RESOLVED_LOG_PATH):
            return jsonify({'success': True, 'logs': 'Nessun log presente.'})
        try:
            with open(RESOLVED_LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                last_lines = lines[-150:]
                return jsonify({'success': True, 'logs': ''.join(last_lines)})
        except Exception as e:
            app.logger.error(f"Errore durante la lettura del file di log: {e}", exc_info=True)
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/settings/logs/download')
    def settings_logs_download():
        directory = os.path.dirname(RESOLVED_LOG_PATH)
        filename = os.path.basename(RESOLVED_LOG_PATH)
        if not os.path.exists(RESOLVED_LOG_PATH):
            flash("File di log di sistema non ancora generato.", "error")
            return redirect(url_for('settings'))
        app.logger.info("Download avviato per il file di log di sistema completo app.log")
        return send_from_directory(directory, filename, as_attachment=True)

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
