# ============================================================
#  app/services/producto_service.py
#  CRUD de productos y categorias
# ============================================================
from typing import List, Optional
from app.database.connection import DatabaseConnection
from app.services.permisos import Permisos, ServicioProtegido


class ProductoService(ServicioProtegido):
    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth
        # Importar caché
        from app.utils.cache import obtener_cache
        self._cache = obtener_cache()

    # ---- Categorias ----
    def listar_categorias(self) -> List[dict]:
        """OPTIMIZADO: Con caché de 5 minutos."""
        cache_key = "categorias:all"
        resultado = self._cache.get(cache_key)
        if resultado is not None:
            return resultado
        
        resultado = self._db.fetchall("SELECT * FROM categorias ORDER BY nombre;")
        self._cache.set(cache_key, resultado, ttl_segundos=300)
        return resultado

    def crear_categoria(self, nombre: str) -> int:
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        c = self._db.execute(
            "INSERT OR IGNORE INTO categorias (nombre) VALUES (?);", (nombre,)
        )
        self._db.commit()
        # Invalidar caché
        self._cache.invalidar("categorias:all")
        return c.lastrowid

    # ---- Productos ----
    def listar_activos(self) -> List[dict]:
        """OPTIMIZADO: Con caché de 5 minutos."""
        cache_key = "productos:activos"
        resultado = self._cache.get(cache_key)
        if resultado is not None:
            return resultado
        
        resultado = self._db.fetchall(
            """SELECT p.*, c.nombre AS categoria_nombre
               FROM productos p
               LEFT JOIN categorias c ON p.categoria_id = c.id
               WHERE p.activo = 1
               ORDER BY p.nombre;"""
        )
        self._cache.set(cache_key, resultado, ttl_segundos=300)
        return resultado

    def listar_todos(self) -> List[dict]:
        """OPTIMIZADO: Con caché de 5 minutos."""
        cache_key = "productos:todos"
        resultado = self._cache.get(cache_key)
        if resultado is not None:
            return resultado
        
        resultado = self._db.fetchall(
            """SELECT p.*, c.nombre AS categoria_nombre
               FROM productos p
               LEFT JOIN categorias c ON p.categoria_id = c.id
               ORDER BY p.nombre;"""
        )
        self._cache.set(cache_key, resultado, ttl_segundos=300)
        return resultado

    def listar_inactivos(self) -> List[dict]:
        """Lista productos desactivados (activo = 0)."""
        resultado = self._db.fetchall(
            """SELECT p.*, c.nombre AS categoria_nombre
               FROM productos p
               LEFT JOIN categorias c ON p.categoria_id = c.id
               WHERE p.activo = 0
               ORDER BY p.nombre;"""
        )
        return resultado

    def obtener_por_id(self, id: int) -> Optional[dict]:
        """OPTIMIZADO: Con caché de 10 minutos por producto."""
        cache_key = f"producto:{id}"
        resultado = self._cache.get(cache_key)
        if resultado is not None:
            return resultado
        
        resultado = self._db.fetchone(
            """SELECT p.*, c.nombre AS categoria_nombre
               FROM productos p
               LEFT JOIN categorias c ON p.categoria_id = c.id
               WHERE p.id = ?;""",
            (id,),
        )
        if resultado:
            self._cache.set(cache_key, resultado, ttl_segundos=600)
        return resultado

    def crear(self, nombre: str, descripcion: str, categoria_id: Optional[int], precio: float) -> int:
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        c = self._db.execute(
            """INSERT INTO productos (nombre, descripcion, categoria_id, precio)
               VALUES (?,?,?,?);""",
            (nombre, descripcion, categoria_id, precio),
        )
        self._db.commit()
        # Invalidar cachés relacionados
        self._cache.invalidar("productos:activos")
        self._cache.invalidar("productos:todos")
        return c.lastrowid

    def actualizar(self, id: int, nombre: str, descripcion: str, categoria_id: Optional[int], precio: float):
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        self._db.execute(
            """UPDATE productos
               SET nombre=?, descripcion=?, categoria_id=?, precio=?,
                   fecha_modificacion=datetime('now','localtime')
               WHERE id=?;""",
            (nombre, descripcion, categoria_id, precio, id),
        )
        self._db.commit()
        # Invalidar cachés relacionados
        self._cache.invalidar(f"producto:{id}")
        self._cache.invalidar("productos:activos")
        self._cache.invalidar("productos:todos")

    def cambiar_estado(self, id: int, activo: bool):
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        self._db.execute(
            "UPDATE productos SET activo=? WHERE id=?;", (1 if activo else 0, id)
        )
        self._db.commit()
        # Invalidar cachés relacionados
        self._cache.invalidar(f"producto:{id}")
        self._cache.invalidar("productos:activos")
        self._cache.invalidar("productos:todos")

    def cambiar_precio(self, id: int, nuevo_precio: float):
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        self._db.execute(
            """UPDATE productos
               SET precio=?, fecha_modificacion=datetime('now','localtime')
               WHERE id=?;""",
            (nuevo_precio, id),
        )
        self._db.commit()
        # Invalidar cachés relacionados
        self._cache.invalidar(f"producto:{id}")
        self._cache.invalidar("productos:activos")
        self._cache.invalidar("productos:todos")

    def eliminar(self, id: int):
        """Marca un producto como INACTIVO (no eliminable si tiene historial)."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        try:
            # Simplemente marcar como inactivo en lugar de eliminar
            # Esto preserva la integridad del historial
            self._db.execute(
                "UPDATE productos SET activo=0 WHERE id=?;",
                (id,)
            )
            self._db.commit()
        except Exception as e:
            self._db.rollback()
            raise Exception(f"No se pudo desactivar el producto: {str(e)}")
        
        # Invalidar cachés relacionados
        self._cache.invalidar(f"producto:{id}")
        self._cache.invalidar("productos:activos")
        self._cache.invalidar("productos:todos")

    def reactivar(self, id: int):
        """Reactiva un producto desactivado (marcado como inactivo)."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        try:
            self._db.execute(
                "UPDATE productos SET activo=1 WHERE id=?;",
                (id,)
            )
            self._db.commit()
        except Exception as e:
            self._db.rollback()
            raise Exception(f"No se pudo reactivar el producto: {str(e)}")
        
        # Invalidar cachés relacionados
        self._cache.invalidar(f"producto:{id}")
        self._cache.invalidar("productos:activos")
        self._cache.invalidar("productos:todos")
