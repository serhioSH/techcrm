# ============================================================
#  app/utils/paths.py
#  Rutas absolutas del proyecto (base de datos, carpetas)
# ============================================================
import os
import sys


def _base_dir() -> str:
    """Retorna la carpeta raiz del proyecto, sea .py o .exe (PyInstaller)."""
    if getattr(sys, "frozen", False):
        # Ejecutando como .exe con PyInstaller
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


BASE_DIR           = _base_dir()
DATA_DIR           = os.path.join(BASE_DIR, "data")
DB_PATH            = os.path.join(DATA_DIR, "pos.db")
COMPROBANTES_PATH  = os.path.join(BASE_DIR, "comprobantes")
REPORTES_PATH      = os.path.join(BASE_DIR, "reportes")
BACKUPS_PATH       = os.path.join(BASE_DIR, "backups")
LOGS_PATH          = os.path.join(BASE_DIR, "logs")
CONFIG_PATH        = os.path.join(BASE_DIR, "configuracion")
ASSETS_PATH        = os.path.join(CONFIG_PATH, "assets")
LOGO_PATH          = os.path.join(ASSETS_PATH, "logo")

# Crear directorios si no existen
for _d in [DATA_DIR, COMPROBANTES_PATH, REPORTES_PATH,
           BACKUPS_PATH, LOGS_PATH, LOGO_PATH]:
    os.makedirs(_d, exist_ok=True)
