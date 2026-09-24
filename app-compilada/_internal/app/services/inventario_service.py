# ============================================================
#  app/services/inventario_service.py
#  Gestion de materias primas e inventario
# ============================================================
from typing import List, Optional
from app.database.connection import DatabaseConnection
from app.services.permisos import Permisos, ServicioProtegido


class MateriaPrimaService(ServicioProtegido):
    """Gestiona materias primas (carne, salchichas, ingredientes, etc)."""
    
    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth

    def listar_activas(self) -> List[dict]:
        """Lista materias primas activas."""
        return self._db.fetchall(
            "SELECT * FROM materias_primas WHERE activo=1 ORDER BY nombre;"
        )

    def listar_todas(self) -> List[dict]:
        """Lista todas las materias primas (incluye desactivadas)."""
        return self._db.fetchall(
            "SELECT * FROM materias_primas ORDER BY nombre;"
        )

    def obtener_por_id(self, id: int) -> Optional[dict]:
        """Obtiene una materia prima por ID."""
        return self._db.fetchone(
            "SELECT * FROM materias_primas WHERE id=?;", (id,)
        )

    def crear(self, nombre: str, descripcion: str = "", stock_inicial: int = 0) -> int:
        """Crea una nueva materia prima."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        c = self._db.execute(
            """INSERT INTO materias_primas (nombre, descripcion, stock, activo)
               VALUES (?, ?, ?, 1);""",
            (nombre, descripcion, max(0, stock_inicial)),
        )
        self._db.commit()
        return c.lastrowid

    def actualizar(self, id: int, nombre: str = None, descripcion: str = None) -> bool:
        """Actualiza nombre/descripción de una materia prima."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        updates = []
        params = []
        
        if nombre is not None:
            updates.append("nombre=?")
            params.append(nombre)
        
        if descripcion is not None:
            updates.append("descripcion=?")
            params.append(descripcion)
        
        if not updates:
            return False
        
        updates.append("fecha_actualizacion=datetime('now','localtime')")
        params.append(id)
        
        self._db.execute(
            f"UPDATE materias_primas SET {', '.join(updates)} WHERE id=?;",
            params,
        )
        self._db.commit()
        return True

    def actualizar_stock(self, id: int, nuevo_stock: int) -> bool:
        """Actualiza el stock de una materia prima."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        self._db.execute(
            "UPDATE materias_primas SET stock=?, fecha_actualizacion=datetime('now','localtime') WHERE id=?;",
            (max(0, nuevo_stock), id),
        )
        self._db.commit()
        return True

    def aumentar_stock(self, id: int, cantidad: int) -> bool:
        """Aumenta stock de una materia prima."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        mp = self.obtener_por_id(id)
        if not mp:
            return False
        
        nuevo_stock = mp["stock"] + cantidad
        return self.actualizar_stock(id, nuevo_stock)

    def disminuir_stock(self, id: int, cantidad: int) -> bool:
        """Disminuye stock de una materia prima."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        mp = self.obtener_por_id(id)
        if not mp:
            return False
        
        nuevo_stock = max(0, mp["stock"] - cantidad)
        return self.actualizar_stock(id, nuevo_stock)

    def eliminar(self, id: int) -> bool:
        """Marca materia prima como inactiva."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        self._db.execute(
            "UPDATE materias_primas SET activo=0 WHERE id=?;", (id,)
        )
        self._db.commit()
        return True


class EmpaquesDomicilioService(ServicioProtegido):
    """Gestiona empaques para entregas a domicilio (stock obligatorio)."""
    
    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth

    # ---- CRUD de Empaques ----
    def listar_activos(self) -> List[dict]:
        """Lista empaques activos disponibles."""
        return self._db.fetchall(
            "SELECT * FROM empaques_domicilio WHERE activo=1 ORDER BY nombre;"
        )

    def listar_todos(self) -> List[dict]:
        """Lista todos los empaques (incluye desactivados)."""
        return self._db.fetchall(
            "SELECT * FROM empaques_domicilio ORDER BY nombre;"
        )

    def obtener_por_id(self, empaque_id: int) -> Optional[dict]:
        """Obtiene empaque por ID."""
        return self._db.fetchone(
            "SELECT * FROM empaques_domicilio WHERE id=?;", (empaque_id,)
        )

    def crear(self, nombre: str, descripcion: str = "", stock_inicial: int = 0) -> int:
        """Crea un nuevo tipo de empaque."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        c = self._db.execute(
            """INSERT INTO empaques_domicilio (nombre, descripcion, stock, activo)
               VALUES (?, ?, ?, 1);""",
            (nombre, descripcion, max(0, stock_inicial)),
        )
        self._db.commit()
        return c.lastrowid

    def actualizar(self, empaque_id: int, nombre: str = None, descripcion: str = None) -> bool:
        """Actualiza nombre/descripción de un empaque."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        updates = []
        params = []
        
        if nombre is not None:
            updates.append("nombre=?")
            params.append(nombre)
        
        if descripcion is not None:
            updates.append("descripcion=?")
            params.append(descripcion)
        
        if not updates:
            return False
        
        updates.append("fecha_actualizacion=datetime('now','localtime')")
        params.append(empaque_id)
        
        self._db.execute(
            f"UPDATE empaques_domicilio SET {', '.join(updates)} WHERE id=?;",
            params,
        )
        self._db.commit()
        return True

    def eliminar(self, empaque_id: int) -> bool:
        """Marca empaque como inactivo (no eliminación física)."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        self._db.execute(
            "UPDATE empaques_domicilio SET activo=0 WHERE id=?;", (empaque_id,)
        )
        self._db.commit()
        return True

    # ---- Gestión de Stock de Empaques ----
    def actualizar_stock(self, empaque_id: int, nuevo_stock: int) -> bool:
        """Actualiza stock de un empaque."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        self._db.execute(
            "UPDATE empaques_domicilio SET stock=?, fecha_actualizacion=datetime('now','localtime') WHERE id=?;",
            (max(0, nuevo_stock), empaque_id),
        )
        self._db.commit()
        return True

    def aumentar_stock(self, empaque_id: int, cantidad: int) -> bool:
        """Aumenta stock de un empaque."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        empaque = self.obtener_por_id(empaque_id)
        if not empaque:
            return False
        
        nuevo_stock = empaque["stock"] + cantidad
        return self.actualizar_stock(empaque_id, nuevo_stock)

    def disminuir_stock(self, empaque_id: int, cantidad: int) -> bool:
        """Disminuye stock de un empaque."""
        self._requerir(Permisos.ADMINISTRAR_PRODUCTOS)
        
        empaque = self.obtener_por_id(empaque_id)
        if not empaque:
            return False
        
        nuevo_stock = max(0, empaque["stock"] - cantidad)
        return self.actualizar_stock(empaque_id, nuevo_stock)

    def tiene_stock(self, empaque_id: int, cantidad: int = 1) -> bool:
        """Verifica si hay stock disponible de un empaque."""
        empaque = self.obtener_por_id(empaque_id)
        return empaque is not None and empaque["stock"] >= cantidad

    # ---- Registro de Empaques Usados en Ventas ----
    def registrar_empaque_venta(self, venta_id: int, empaque_id: int, cantidad: int = 1) -> bool:
        """Registra qué empaque se usó en una venta a domicilio."""
        # No requiere permiso: se registra automáticamente al cobrar
        
        self._db.execute(
            """INSERT INTO ventas_empaques (venta_id, empaque_id, cantidad_usada)
               VALUES (?, ?, ?);""",
            (venta_id, empaque_id, cantidad),
        )
        self._db.commit()
        return True

    def obtener_empaque_venta(self, venta_id: int) -> Optional[dict]:
        """Obtiene el empaque usado en una venta."""
        return self._db.fetchone(
            """SELECT ve.*, e.nombre AS empaque_nombre
               FROM ventas_empaques ve
               LEFT JOIN empaques_domicilio e ON ve.empaque_id = e.id
               WHERE ve.venta_id=?;""",
            (venta_id,),
        )


class SnapshotInventarioService(ServicioProtegido):
    """Gestiona snapshots (historial) del inventario al cierre de caja."""
    
    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth

    def guardar_snapshot(self, caja_id: int, nota: str = "") -> int:
        """Guarda un snapshot de materias primas y empaques al cierre de caja."""
        # No requiere permiso especial: se llama automáticamente
        
        import json
        
        # Obtener estado actual de materias primas
        materias_primas = self._db.fetchall(
            """SELECT id, nombre, descripcion, stock, activo, fecha_actualizacion
               FROM materias_primas
               ORDER BY nombre;"""
        )
        
        # Obtener estado actual de empaques
        empaques = self._db.fetchall(
            """SELECT id, nombre, descripcion, stock, activo, fecha_actualizacion
               FROM empaques_domicilio
               ORDER BY nombre;"""
        )
        
        # Convertir a JSON
        snapshot_data = {
            "materias_primas": [dict(row) for row in materias_primas],
            "empaques": [dict(row) for row in empaques]
        }
        datos_json = json.dumps(snapshot_data, ensure_ascii=False, indent=2)
        
        # Guardar snapshot
        usuario_id = self._auth.usuario_actual.id if self._auth and self._auth.usuario_actual else None
        
        c = self._db.execute(
            """INSERT INTO inventario_snapshots (caja_id, datos_json, nota, usuario_id)
               VALUES (?, ?, ?, ?);""",
            (caja_id, datos_json, nota.strip(), usuario_id),
        )
        self._db.commit()
        return c.lastrowid

    def listar_snapshots(self, caja_id: int = None) -> List[dict]:
        """Lista snapshots del inventario."""
        if caja_id:
            return self._db.fetchall(
                """SELECT s.*, c.estado AS caja_estado, u.nombre AS usuario_nombre
                   FROM inventario_snapshots s
                   LEFT JOIN cajas c ON s.caja_id = c.id
                   LEFT JOIN usuarios u ON s.usuario_id = u.id
                   WHERE s.caja_id=?
                   ORDER BY s.fecha_snapshot DESC;""",
                (caja_id,),
            )
        else:
            return self._db.fetchall(
                """SELECT s.*, c.estado AS caja_estado, u.nombre AS usuario_nombre
                   FROM inventario_snapshots s
                   LEFT JOIN cajas c ON s.caja_id = c.id
                   LEFT JOIN usuarios u ON s.usuario_id = u.id
                   ORDER BY s.fecha_snapshot DESC;"""
            )

    def obtener_snapshot(self, snapshot_id: int) -> Optional[dict]:
        """Obtiene un snapshot específico con sus datos."""
        return self._db.fetchone(
            """SELECT s.*, c.estado AS caja_estado, u.nombre AS usuario_nombre
               FROM inventario_snapshots s
               LEFT JOIN cajas c ON s.caja_id = c.id
               LEFT JOIN usuarios u ON s.usuario_id = u.id
               WHERE s.id=?;""",
            (snapshot_id,),
        )
