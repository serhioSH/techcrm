# ============================================================
#  app/services/configuracion_service.py
#  Lectura y escritura de configuracion del negocio en SQLite
# ============================================================
from app.database.connection import DatabaseConnection
from app.services.permisos import Permisos, ServicioProtegido


class ConfiguracionService(ServicioProtegido):
    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth

    def get(self, clave: str, default: str = "") -> str:
        row = self._db.fetchone(
            "SELECT valor FROM configuracion WHERE clave=?;", (clave,)
        )
        return row["valor"] if row else default

    def set(self, clave: str, valor: str):
        self._requerir(Permisos.MODIFICAR_CONFIGURACION)
        
        # Si se cambia el logo, limpiar caché de impresión
        if clave == "logo_path":
            try:
                from app.printing import escpos
                escpos.limpiar_cache_logos()
            except:
                pass  # Si falla, no es crítico
        
        self._db.execute(
            "INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?,?);",
            (clave, valor),
        )
        self._db.commit()

    def get_todos(self) -> dict:
        rows = self._db.fetchall("SELECT clave, valor FROM configuracion;")
        return {r["clave"]: r["valor"] for r in rows}

    def set_varios(self, datos: dict):
        self._requerir(Permisos.MODIFICAR_CONFIGURACION)
        for clave, valor in datos.items():
            self.set(clave, valor)
