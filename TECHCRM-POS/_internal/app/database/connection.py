# ============================================================
#  app/database/connection.py
#  Gestor de conexion SQLite — unica fuente de verdad
# ============================================================
import sqlite3
import os
import threading
from app.utils.paths import DB_PATH


class DatabaseConnection:
    """
    Singleton thread-safe para la conexion a SQLite.
    Gestiona la conexion y provee metodos auxiliares.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._db_path = DB_PATH
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._connection = None
        self._connect()
        self._initialized = True

    def _connect(self):
        """Establece la conexion con SQLite habilitando claves foraneas."""
        self._connection = sqlite3.connect(
            self._db_path,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON;")
        self._connection.execute("PRAGMA journal_mode = WAL;")
        self._connection.commit()

    @property
    def connection(self) -> sqlite3.Connection:
        """Retorna la conexion activa."""
        return self._connection

    def cursor(self) -> sqlite3.Cursor:
        """Retorna un nuevo cursor."""
        return self._connection.cursor()

    def commit(self):
        """Confirma la transaccion actual."""
        self._connection.commit()

    def rollback(self):
        """Revierte la transaccion actual."""
        self._connection.rollback()

    def close(self):
        """Cierra la conexion de forma segura."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def execute(self, sql: str, params=()) -> sqlite3.Cursor:
        """Ejecuta una sentencia SQL y retorna el cursor."""
        cursor = self._connection.cursor()
        cursor.execute(sql, params)
        return cursor

    def fetchall(self, sql: str, params=()) -> list:
        """Ejecuta una consulta y retorna todas las filas como lista de dicts."""
        cursor = self.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def fetchone(self, sql: str, params=()) -> dict | None:
        """Ejecuta una consulta y retorna la primera fila como dict."""
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    # ----------------------------------------------------------
    # Transacciones explicitas (seguridad ante cierres inesperados)
    # ----------------------------------------------------------
    class _Transaccion:
        """Context manager: commit al salir bien, rollback ante cualquier error."""

        def __init__(self, db: "DatabaseConnection"):
            self._db = db

        def __enter__(self):
            return self._db

        def __exit__(self, exc_type, exc, tb):
            if exc_type is None:
                self._db.commit()
            else:
                self._db.rollback()
            return False

    def transaccion(self) -> "DatabaseConnection._Transaccion":
        """
        Uso:
            with db.transaccion():
                db.execute(...)
                db.execute(...)
        Si algo falla dentro del bloque, se revierte todo automaticamente.
        """
        return DatabaseConnection._Transaccion(self)

    def integrity_check(self) -> str:
        """Ejecuta PRAGMA integrity_check y retorna el resultado."""
        row = self.fetchone("PRAGMA integrity_check;")
        return row.get("integrity_check", "unknown") if row else "unknown"

    def foreign_key_check(self) -> list:
        """Retorna las violaciones de claves foraneas (lista vacia si no hay)."""
        return self.fetchall("PRAGMA foreign_key_check;")
