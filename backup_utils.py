import os
import glob
import time
import shutil
import logging
from datetime import datetime
from config import DB_PATH, BACKUP_DIR

logger = logging.getLogger(__name__)

def esegui_rotazione_backups():
    """
    Mantiene solo gli ultimi 30 file di backup più recenti ordinati per timestamp nel nome file.
    """
    try:
        if not os.path.exists(BACKUP_DIR):
            return
            
        # Trova tutti i backup .db
        backups = glob.glob(os.path.join(BACKUP_DIR, "database_backup_*.db"))
        # Ordinamento alfabetico (grazie a YYYYMMDD_HHMMSS equivale a cronologico)
        backups.sort()
        
        # Se superano i 30, eliminiamo quelli in più a partire dal più vecchio
        if len(backups) > 30:
            to_delete = backups[:-30]
            for file_path in to_delete:
                try:
                    os.remove(file_path)
                    logger.info(f"Rotazione backup: rimosso vecchio file {file_path}")
                except Exception as ex:
                    logger.error(f"Errore durante l'eliminazione del vecchio backup {file_path}: {ex}")
            logger.info(f"Rotazione backup eseguita. Rimossi {len(to_delete)} backup in eccesso.")
    except Exception as e:
        logger.error(f"Errore critico durante la rotazione dei backup: {e}", exc_info=True)


def ciclo_backup_background():
    """
    Ciclo continuo in background per garantire almeno un backup al giorno.
    Controlla periodicamente (ogni ora) e genera un backup se manca quello per il giorno corrente.
    """
    # Ritardo iniziale all'avvio per non rallentare il bootstrap iniziale di Flask
    time.sleep(5)
    
    # Esegui subito una rotazione iniziale per pulire la cartella se piena al boot
    esegui_rotazione_backups()
    
    if not os.path.exists(BACKUP_DIR):
        try:
            os.makedirs(BACKUP_DIR)
        except Exception as e:
            logger.error(f"[BACKUP AUTOMATICO] Impossibile creare la cartella di backup: {e}", exc_info=True)
            return

    while True:
        try:
            today_str = datetime.now().strftime('%Y%m%d')
            
            # Cerca se esiste già un backup per oggi
            today_backups = glob.glob(os.path.join(BACKUP_DIR, f"database_backup_{today_str}_*.db"))
            if not today_backups:
                src_db = DB_PATH
                if os.path.exists(src_db):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    dst_db = os.path.join(BACKUP_DIR, f"database_backup_{timestamp}.db")
                    shutil.copy2(src_db, dst_db)
                    logger.info(f"Backup automatico programmato creato con successo: database_backup_{timestamp}.db")
                    
                    # Riapri la rotazione per mantenere solo 30 file
                    esegui_rotazione_backups()
                else:
                    logger.warning("[BACKUP AUTOMATICO] Attenzione: file database attivo non trovato!")
        except Exception as e:
            logger.error(f"[BACKUP AUTOMATICO] Errore nel ciclo di background: {e}", exc_info=True)
            
        # Attendi un'ora (3600 secondi) prima del controllo successivo
        time.sleep(3600)


def avvia_schedulatore_backup(app_debug):
    """
    Avvia il thread demone per il backup in background.
    Se Flask è in modalità debug, assicura di avviarsi una sola volta.
    """
    import threading
    # Avvia solo sul processo principale se in modalità debug (Werkzeug reloader)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app_debug:
        t = threading.Thread(target=ciclo_backup_background, daemon=True)
        t.start()
        logger.info("Thread di controllo e backup automatico in background avviato con successo.")
