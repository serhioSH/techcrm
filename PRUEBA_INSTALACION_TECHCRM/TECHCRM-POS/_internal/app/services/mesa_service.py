# ============================================================
#  app/services/mesa_service.py
#  Gestion de mesas
# ============================================================
from typing import List, Optional
from app.database.connection import DatabaseConnection
from app.services.permisos import Permisos, ServicioProtegido


class MesaService(ServicioProtegido):
    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth
        # Importar caché
        from app.utils.cache import obtener_cache
        self._cache = obtener_cache()

    def listar(self) -> List[dict]:
        """OPTIMIZADO: Con caché de 10 segundos (cambia frecuentemente)."""
        # Limpiar mesas inconsistentes primero
        self._limpiar_inconsistencias()
        
        cache_key = "mesas:todas"
        resultado = self._cache.get(cache_key)
        if resultado is not None:
            return resultado
        
        # Migración V6: venta_activa_id column removed. Join on mesa_id with ABIERTA ventas instead
        resultado = self._db.fetchall(
            """SELECT m.*, v.id AS venta_activa_id, v.consecutivo AS venta_consecutivo,
                      v.cliente AS venta_cliente,
                      v.direccion_entrega AS venta_direccion
               FROM mesas m
               LEFT JOIN ventas v ON m.id = v.mesa_id AND v.estado = 'ABIERTA'
               ORDER BY m.tipo DESC, m.id;"""
        )
        self._cache.set(cache_key, resultado, ttl_segundos=10)
        return resultado

    def _limpiar_inconsistencias(self):
        """Limpia mesas que están OCUPADAS pero no tienen ventas ABIERTA.
        Migración V6: venta_activa_id column removed, so we check via LEFT JOIN."""
        self._db.execute(
            """UPDATE mesas SET estado='DISPONIBLE'
               WHERE estado='OCUPADA' 
               AND id NOT IN (SELECT DISTINCT mesa_id FROM ventas WHERE estado='ABIERTA');"""
        )
        self._db.commit()
        
        # Limpiar domicilios vacíos dejando al menos 1 disponible
        self._limpiar_domicilios_vacios()

    def _limpiar_domicilios_vacios(self):
        """Elimina domicilios vacíos (sin ventas ABIERTA) dejando solo 1 disponible.
        Luego renumera los domicilios restantes de forma secuencial (1, 2, 3...)."""
        # Contar domicilios disponibles y vacíos
        domicilios_vacios = self._db.fetchall(
            """SELECT m.id FROM mesas m
               WHERE m.tipo = 'DOMICILIO' 
               AND m.estado = 'DISPONIBLE'
               AND m.id NOT IN (SELECT DISTINCT mesa_id FROM ventas WHERE estado='ABIERTA')
               ORDER BY m.id DESC;"""
        )
        
        # Dejar solo 1 disponible vacío, eliminar el resto
        hubo_eliminacion = False
        if len(domicilios_vacios) > 1:
            ids_a_eliminar = [d["id"] for d in domicilios_vacios[1:]]  # Todos excepto el primero
            for domicilio_id in ids_a_eliminar:
                try:
                    self._db.execute("DELETE FROM mesas WHERE id=?;", (domicilio_id,))
                    hubo_eliminacion = True
                except Exception:
                    pass  # Si falla por FK, simplemente ignorar
            if hubo_eliminacion:
                self._db.commit()
                # Invalidar caché después de eliminar
                self._cache.invalidar("mesas:todas")
                # Renumerar domicilios solo si se eliminó algo
                self._renumerar_domicilios()

    def _renumerar_domicilios(self):
        """Renumera los domicilios de forma secuencial: Domicilio 1, 2, 3..."""
        domicilios = self._db.fetchall(
            "SELECT id FROM mesas WHERE tipo = 'DOMICILIO' ORDER BY id;"
        )
        for numero, domicilio in enumerate(domicilios, start=1):
            self._db.execute(
                "UPDATE mesas SET nombre=? WHERE id=?;",
                (f"Domicilio {numero}", domicilio["id"])
            )
        self._db.commit()
        self._cache.invalidar("mesas:todas")

    def obtener_por_id(self, id: int) -> Optional[dict]:
        """OPTIMIZADO: Con caché de 1 minuto."""
        cache_key = f"mesa:{id}"
        resultado = self._cache.get(cache_key)
        if resultado is not None:
            return resultado
        
        resultado = self._db.fetchone("SELECT * FROM mesas WHERE id=?;", (id,))
        if resultado:
            self._cache.set(cache_key, resultado, ttl_segundos=60)
        return resultado

    def crear(self, nombre: str, tipo: str = "MESA") -> int:
        self._requerir(Permisos.ADMINISTRAR_MESAS)
        tipo = (tipo or "MESA").upper()
        if tipo not in ("MESA", "DOMICILIO"):
            raise ValueError("Tipo de mesa invalido: use MESA o DOMICILIO.")
        c = self._db.execute(
            "INSERT INTO mesas (nombre, tipo) VALUES (?, ?);", (nombre, tipo)
        )
        self._db.commit()
        # Invalidar caché
        self._cache.invalidar("mesas:todas")
        return c.lastrowid

    # ---- Mesas de domicilio (creacion automatica del sistema) ----
    def hay_domicilio_disponible(self) -> bool:
        fila = self._db.fetchone(
            "SELECT COUNT(*) AS n FROM mesas "
            "WHERE tipo = 'DOMICILIO' AND estado = 'DISPONIBLE';"
        )
        return bool(fila and fila["n"] > 0)

    def siguiente_numero_domicilio(self) -> int:
        """Retorna el siguiente número secuencial para domicilios (siempre en orden 1, 2, 3...)."""
        filas = self._db.fetchall(
            "SELECT COUNT(*) as n FROM mesas WHERE tipo = 'DOMICILIO';"
        )
        count = filas[0]["n"] if filas else 0
        return count + 1

    def crear_domicilio_automatico(self) -> int:
        """Crea una mesa de domicilio vacia (no exige permisos de
        administracion: es comportamiento automatico del negocio)."""
        numero = self.siguiente_numero_domicilio()
        c = self._db.execute(
            "INSERT INTO mesas (nombre, estado, tipo) "
            "VALUES (?, 'DISPONIBLE', 'DOMICILIO');",
            (f"Domicilio {numero}",),
        )
        self._db.commit()
        # Invalidar caché
        self._cache.invalidar("mesas:todas")
        return c.lastrowid

    def actualizar_nombre(self, id: int, nombre: str):
        self._requerir(Permisos.ADMINISTRAR_MESAS)
        self._db.execute("UPDATE mesas SET nombre=? WHERE id=?;", (nombre, id))
        self._db.commit()
        # Invalidar cachés relacionados
        self._cache.invalidar(f"mesa:{id}")
        self._cache.invalidar("mesas:todas")

    def eliminar(self, id: int):
        self._requerir(Permisos.ADMINISTRAR_MESAS)
        self._db.execute("DELETE FROM mesas WHERE id=?;", (id,))
        self._db.commit()
        # Invalidar cachés
        self._cache.invalidar(f"mesa:{id}")
        self._cache.invalidar("mesas:todas")

    def ocupar(self, mesa_id: int, venta_id: int):
        self._requerir(Permisos.USAR_MESAS)
        # Migración V6: venta_activa_id column removed. Mesa state indicates ocupancy,
        # and we find the venta via LEFT JOIN on mesa_id with estado='ABIERTA'
        self._db.execute(
            "UPDATE mesas SET estado='OCUPADA' WHERE id=?;",
            (mesa_id,),
        )
        self._db.commit()
        # Invalidar caché (cambió el estado)
        self._cache.invalidar(f"mesa:{mesa_id}")
        self._cache.invalidar("mesas:todas")

    def liberar(self, mesa_id: int):
        self._requerir(Permisos.USAR_MESAS)
        self._db.execute(
            "UPDATE mesas SET estado='DISPONIBLE' WHERE id=?;",
            (mesa_id,),
        )
        self._db.commit()
        # Invalidar caché (cambió el estado)
        self._cache.invalidar(f"mesa:{mesa_id}")
        self._cache.invalidar("mesas:todas")
