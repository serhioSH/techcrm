# ============================================================
#  app/services/venta_service.py
#  Gestion completa de ventas y detalles
# ============================================================
from typing import List, Optional
from app.database.connection import DatabaseConnection
from app.services.permisos import Permisos, ServicioProtegido


class VentaService(ServicioProtegido):
    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth

    # ---- Creacion / apertura ----
    def abrir_venta(self, mesa_id: int, usuario_id: int, caja_id: Optional[int]) -> int:
        """Crea una venta en estado ABIERTA y retorna su ID."""
        self._requerir(Permisos.USAR_MESAS)
        consecutivo = self._siguiente_consecutivo()
        c = self._db.execute(
            """INSERT INTO ventas (consecutivo, mesa_id, usuario_id, caja_id)
               VALUES (?,?,?,?);""",
            (consecutivo, mesa_id, usuario_id, caja_id),
        )
        self._db.commit()
        return c.lastrowid

    def _siguiente_consecutivo(self) -> int:
        row = self._db.fetchone("SELECT MAX(consecutivo) AS max_c FROM ventas;")
        return (row["max_c"] or 0) + 1

    # ---- Detalles ----
    def agregar_detalle(self, venta_id: int, producto_id: int, nombre: str,
                        cantidad: float, precio: float) -> int:
        self._requerir(Permisos.USAR_MESAS)
        subtotal = round(cantidad * precio, 2)
        # Si ya existe el producto en el detalle, actualizar cantidad
        existente = self._db.fetchone(
            "SELECT id, cantidad FROM detalle_ventas WHERE venta_id=? AND producto_id=?;",
            (venta_id, producto_id),
        )
        if existente:
            nueva_cant = existente["cantidad"] + cantidad
            nuevo_sub  = round(nueva_cant * precio, 2)
            self._db.execute(
                "UPDATE detalle_ventas SET cantidad=?, subtotal=? WHERE id=?;",
                (nueva_cant, nuevo_sub, existente["id"]),
            )
        else:
            self._db.execute(
                """INSERT INTO detalle_ventas
                   (venta_id, producto_id, nombre_producto, cantidad, precio_unitario, subtotal)
                   VALUES (?,?,?,?,?,?);""",
                (venta_id, producto_id, nombre, cantidad, precio, subtotal),
            )
        self._recalcular_totales(venta_id)
        self._db.commit()
        return venta_id

    def actualizar_cantidad_detalle(self, detalle_id: int, cantidad: float):
        self._requerir(Permisos.USAR_MESAS)
        row = self._db.fetchone(
            "SELECT venta_id, precio_unitario FROM detalle_ventas WHERE id=?;",
            (detalle_id,),
        )
        if not row:
            return
        if cantidad <= 0:
            self.eliminar_detalle(detalle_id)
            return
        nuevo_sub = round(cantidad * row["precio_unitario"], 2)
        self._db.execute(
            "UPDATE detalle_ventas SET cantidad=?, subtotal=? WHERE id=?;",
            (cantidad, nuevo_sub, detalle_id),
        )
        self._recalcular_totales(row["venta_id"])
        self._db.commit()

    def eliminar_detalle(self, detalle_id: int):
        self._requerir(Permisos.USAR_MESAS)
        row = self._db.fetchone(
            "SELECT venta_id FROM detalle_ventas WHERE id=?;", (detalle_id,)
        )
        self._db.execute("DELETE FROM detalle_ventas WHERE id=?;", (detalle_id,))
        if row:
            self._recalcular_totales(row["venta_id"])
        self._db.commit()

    def _recalcular_totales(self, venta_id: int):
        row = self._db.fetchone(
            "SELECT COALESCE(SUM(subtotal),0) AS total FROM detalle_ventas WHERE venta_id=?;",
            (venta_id,),
        )
        subtotal = round(row["total"], 2)
        # IMPORTANTE: pasar el subtotal como parametro. En un UPDATE de SQLite,
        # las columnas del lado derecho (subtotal-descuento) se evaluan con el
        # valor ANTIGUO de la fila, no con el nuevo.
        self._db.execute(
            "UPDATE ventas SET subtotal=?, total=?-descuento WHERE id=?;",
            (subtotal, subtotal, venta_id),
        )

    # ---- Cobro ----
    def cobrar(self, venta_id: int, metodo_pago: str) -> bool:
        """
        Cierra la venta. Retorna False si ya fue cobrada (proteccion doble cobro).
        """
        self._requerir(Permisos.COBRAR)
        row = self._db.fetchone(
            "SELECT cobro_procesado, estado FROM ventas WHERE id=?;", (venta_id,)
        )
        if not row or row["cobro_procesado"] == 1 or row["estado"] != "ABIERTA":
            return False
        self._db.execute(
            """UPDATE ventas
               SET estado='CERRADA', metodo_pago=?, cobro_procesado=1,
                   fecha_hora=datetime('now','localtime')
               WHERE id=?;""",
            (metodo_pago, venta_id),
        )
        self._db.commit()
        return True

    def anular(self, venta_id: int) -> bool:
        """
        Anula una venta ABIERTA sin eliminarla (el historial nunca se pierde).
        Retorna False si la venta no existe, ya no esta abierta o ya fue cobrada.
        """
        row = self._db.fetchone(
            "SELECT estado, cobro_procesado FROM ventas WHERE id=?;", (venta_id,)
        )
        if not row or row["estado"] == "ANULADA":
            return False
        if row["estado"] == "ABIERTA":
            self._requerir(Permisos.ANULAR_VENTA_ABIERTA)
        else:
            self._requerir(Permisos.ANULAR_VENTA_CERRADA)
        self._db.execute(
            "UPDATE ventas SET estado='ANULADA' WHERE id=?;", (venta_id,)
        )
        self._db.commit()
        return True


    # ---- Consultas ----
    def obtener_por_id(self, venta_id: int) -> Optional[dict]:
        row = self._db.fetchone(
            """SELECT v.*, m.nombre AS mesa_nombre, u.nombre AS usuario_nombre
               FROM ventas v
               LEFT JOIN mesas m ON v.mesa_id = m.id
               LEFT JOIN usuarios u ON v.usuario_id = u.id
               WHERE v.id=?;""",
            (venta_id,),
        )
        self._validar_propiedad(row)
        return row

    def obtener_detalles(self, venta_id: int) -> List[dict]:
        venta = self._db.fetchone(
            "SELECT usuario_id FROM ventas WHERE id=?;", (venta_id,)
        )
        self._validar_propiedad(venta)
        return self._db.fetchall(
            "SELECT * FROM detalle_ventas WHERE venta_id=? AND cantidad > 0 ORDER BY id;",
            (venta_id,),
        )

    def listar_con_filtros(self, desde: str = None, hasta: str = None,
                           mesa_id: int = None, usuario_id: int = None,
                           metodo_pago: str = None, consecutivo: int = None) -> List[dict]:
        # Punto 3: sin sesion activa no se consulta el historial.
        if self._auth is not None and self._auth.usuario_actual is None:
            raise PermissionError("Debe iniciar sesion para consultar el historial.")
        # Punto 3: un cajero solo consulta SUS ventas; el ADMIN, todas.
        if (self._auth is not None
                and self._auth.usuario_actual is not None
                and not self._auth.puede(Permisos.CONSULTAR_VENTAS)):
            usuario_id = self._auth.usuario_actual.id
        sql = """
            SELECT v.*, m.nombre AS mesa_nombre, u.nombre AS usuario_nombre
            FROM ventas v
            LEFT JOIN mesas m ON v.mesa_id = m.id
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            WHERE v.estado = 'CERRADA'
        """
        params = []
        if desde:
            sql += " AND date(v.fecha_hora) >= ?"
            params.append(desde)
        if hasta:
            sql += " AND date(v.fecha_hora) <= ?"
            params.append(hasta)
        if mesa_id:
            sql += " AND v.mesa_id = ?"
            params.append(mesa_id)
        if usuario_id:
            sql += " AND v.usuario_id = ?"
            params.append(usuario_id)
        if metodo_pago:
            sql += " AND v.metodo_pago = ?"
            params.append(metodo_pago)
        if consecutivo:
            sql += " AND v.consecutivo = ?"
            params.append(consecutivo)
        sql += " ORDER BY v.fecha_hora DESC;"
        return self._db.fetchall(sql, params)

    def _validar_propiedad(self, venta: Optional[dict]):
        """Un cajero solo puede ver y operar SUS ventas."""
        if (venta is not None
                and self._auth is not None
                and self._auth.usuario_actual is not None
                and not self._auth.puede(Permisos.CONSULTAR_VENTAS)
                and venta.get("usuario_id") != self._auth.usuario_actual.id):
            raise PermissionError(
                "Solo puede consultar las ventas que usted realizo.")

    def venta_activa_por_mesa(self, mesa_id: int) -> Optional[dict]:
        return self._db.fetchone(
            "SELECT * FROM ventas WHERE mesa_id=? AND estado='ABIERTA' LIMIT 1;",
            (mesa_id,),
        )
