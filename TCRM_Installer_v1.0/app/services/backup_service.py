# ============================================================
#  app/services/backup_service.py
#  Generacion de backups de la base de datos SQLite
# ============================================================
import os
import sqlite3
from datetime import datetime
from typing import Optional
from app.database.connection import DatabaseConnection
from app.services.permisos import Permisos, ServicioProtegido
from app.utils.paths import BACKUPS_PATH


class BackupService(ServicioProtegido):
    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth

    def crear_backup(self, destino: Optional[str] = None) -> str:
        """
        Copia la base de datos a la carpeta backups/ con timestamp.
        Retorna la ruta del archivo creado.
        """
        self._requerir(Permisos.REALIZAR_BACKUP)
        os.makedirs(BACKUPS_PATH, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = f"backup_pos_{timestamp}.db"
        ruta = destino if destino else os.path.join(BACKUPS_PATH, nombre)

        conn_src = self._db.connection
        conn_dst = sqlite3.connect(ruta)
        conn_src.backup(conn_dst)
        conn_dst.close()
        return ruta

    def listar_backups(self) -> list:
        if not os.path.exists(BACKUPS_PATH):
            return []
        archivos = [f for f in os.listdir(BACKUPS_PATH) if f.endswith(".db")]
        return sorted(archivos, reverse=True)
