import os
import socket
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask

# Importazioni di configurazione e utility modulari
from config import SECRET_KEY, RESOLVED_DB_PATH, RESOLVED_BACKUP_DIR, RESOLVED_LOG_PATH
from db_utils import init_audit_db, init_etichette_db
from backup_utils import avvia_schedulatore_backup
from routes import init_routes

# Creazione e configurazione dell'applicazione Flask
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Assicura la creazione delle cartelle per database e log
os.makedirs(os.path.dirname(RESOLVED_DB_PATH), exist_ok=True)
os.makedirs(os.path.dirname(RESOLVED_LOG_PATH), exist_ok=True)

# Configura il logging centralizzato tramite RotatingFileHandler
log_handler = RotatingFileHandler(
    RESOLVED_LOG_PATH, 
    maxBytes=5*1024*1024,  # 5 MegaBytes
    backupCount=5,
    encoding='utf-8'
)
log_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
log_handler.setLevel(logging.INFO)

# Associa l'handler sia al logger di Flask che a quello radice di Python
app.logger.addHandler(log_handler)
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.INFO)

# Logga l'avvio del server sul processo principale per evitare duplicati in modalità debug
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    app.logger.info("======================================================================")
    app.logger.info("🧪 Gestore-Lab: Avvio dell'applicazione Flask")
    app.logger.info(f"💾 Database attivo: {RESOLVED_DB_PATH}")
    app.logger.info(f"🔄 Cartella backups: {RESOLVED_BACKUP_DIR}")
    app.logger.info(f"📋 File di log: {RESOLVED_LOG_PATH}")
    app.logger.info("======================================================================")

# Inizializza i database SQLite se non esistono
init_audit_db()
init_etichette_db()

# Registra tutte le rotte modulari dell'applicazione
init_routes(app)

# Avvia lo schedulatore automatico dei backup in background
avvia_schedulatore_backup(app.debug)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    flask_host = os.getenv("FLASK_HOST", "0.0.0.0")
    flask_port = int(os.getenv("FLASK_PORT", "5000"))
    flask_debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t", "y", "yes")

    local_ip = get_local_ip()
    print("\n" + "="*70)
    print("  * SERVER APERTO ALLA RETE LOCALE (LAN) *")
    print("  Puoi accedere all'applicazione da smartphone, tablet o altri PC:")
    print(f"  -> http://{local_ip}:{flask_port}")
    print("="*70 + "\n")
    
    app.logger.info(f"Server Web Flask avviato ed in ascolto su http://{local_ip}:{flask_port} (Porta LAN: {flask_port})")
    
    app.run(host=flask_host, port=flask_port, debug=flask_debug)
