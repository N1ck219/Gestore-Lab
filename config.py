import os
from dotenv import load_dotenv

# Carica le variabili di ambiente dal file .env se presente
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "materie_prime_secret")

# Configurazione Database e Directory di Backup
DB_PATH = os.getenv("DB_PATH", os.path.join("database", "database.db"))
BACKUP_DIR = os.getenv("BACKUP_DIR", os.path.join("database", "backups"))

# Configurazione Cartelle per i Documenti PDF Generati
LISTA_DISTRIBUZIONE_DIR = os.getenv("LISTA_DISTRIBUZIONE_DIR", "lista_distribuzione")
RICHIESTA_ANALISI_DIR = os.getenv("RICHIESTA_ANALISI_DIR", "richiesta_analisi")
PICKING_LIST_DIR = os.getenv("PICKING_LIST_DIR", "picking list")

# Configurazione Percorso Log di Sistema
APP_LOG_PATH = os.getenv("APP_LOG_PATH", os.path.join("database", "app.log"))

# Risolve i percorsi in modo relativo alla radice del progetto
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

def resolve_project_path(path):
    if not os.path.isabs(path):
        return os.path.abspath(os.path.join(PROJECT_ROOT, path))
    return path

RESOLVED_DB_PATH = resolve_project_path(DB_PATH)
RESOLVED_BACKUP_DIR = resolve_project_path(BACKUP_DIR)
RESOLVED_LOG_PATH = resolve_project_path(APP_LOG_PATH)
RESOLVED_LISTA_DISTRIBUZIONE_DIR = resolve_project_path(LISTA_DISTRIBUZIONE_DIR)
RESOLVED_RICHIESTA_ANALISI_DIR = resolve_project_path(RICHIESTA_ANALISI_DIR)
RESOLVED_PICKING_LIST_DIR = resolve_project_path(PICKING_LIST_DIR)
