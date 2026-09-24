# ============================================================
#  app/services/system_service.py
#  Servicios de administración del sistema (reinicio BD, etc)
# ============================================================
from app.database.connection import DatabaseConnection
from app.services.permisos import Permisos, ServicioProtegido
from app.database import migrations, seeder


class SystemService(ServicioProtegido):
    """Servicio para operaciones administrativas del sistema."""

    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth

    def reiniciar_base_datos(self) -> dict:
        """
        Reinicia la base de datos: elimina datos operativos pero preserva estructura.
        
        Solo TECNICO (admin del sistema) puede hacer esto.
        """
        self._requerir(Permisos.ADMINISTRAR_SISTEMA)
        
        try:
            # 1. Eliminar datos operativos (en orden de dependencias)
            # FK dependencies: detalles_ventas -> ventas -> mesas; cajas tiene FK a usuarios (no toca)
            
            # Eliminar detalles de venta (FK a ventas)
            self._db.execute("DELETE FROM detalle_ventas;")
            
            # Eliminar ventas (FK a mesas)
            self._db.execute("DELETE FROM ventas;")
            
            # Eliminar cajas
            self._db.execute("DELETE FROM cajas;")
            
            # Eliminar mesas (para recrearlas con valores iniciales)
            self._db.execute("DELETE FROM mesas;")
            
            # Eliminar productos (pero conservar categorías del seeder)
            self._db.execute("DELETE FROM productos;")
            
            self._db.commit()
            
            # 2. Recrear mesas y productos iniciales con seeder
            resultado_seeder = seeder.ejecutar_seeder(self._db)
            
            return {
                "exitoso": True,
                "mensaje": "Base de datos reiniciada correctamente",
                "datos_recreados": resultado_seeder
            }
            
        except Exception as e:
            self._db.rollback()
            return {
                "exitoso": False,
                "mensaje": f"Error durante el reinicio: {str(e)}",
                "error": str(e)
            }
