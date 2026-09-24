import sqlite3
from typing import Optional
from app.database.connection import DatabaseConnection
from app.services.permisos import Permisos, ServicioProtegido, puede as _puede_rol
from app.services.venta_service import VentaService
from app.services.mesa_service import MesaService
from app.services.producto_service import ProductoService


class PedidoService(ServicioProtegido):
    """Orquesta el flujo de una mesa: abrir, tomar, modificar, anular, liberar."""

    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth
        self._ventas = VentaService(db, auth)
        self._mesas = MesaService(db, auth)
        self._productos = ProductoService(db, auth)

    def acceder_mesa(self, id: int, cliente: Optional[str] = None,
                     direccion: Optional[str] = None) -> int:
        """Abre una mesa y retorna el venta_id."""
        return self.abrir_mesa(id, cliente=cliente, direccion=direccion)

    # ---- Mesas ----
    def listar_mesas(self):
        """Solo lectura; no requiere permisos escritura."""
        return self._mesas.listar()

    def obtener_mesa(self, id: int) -> Optional[dict]:
        return self._mesas.obtener_por_id(id)

    def abrir_mesa(self, id: int, usuario_id: Optional[int] = None,
                   cliente: Optional[str] = None,
                   direccion: Optional[str] = None) -> int:
        """
        Abre una mesa DISPONIBLE, la marca OCUPADA y crea una venta
        asociada (estado ABIERTA) retornando el id de la venta.

        Las mesas de DOMICILIO exigen nombre del cliente (direcci´on es opcional
        para clientes cercanos); al ocupar la ultima mesa de domicilio libre se crea
        automaticamente una nueva mesa de domicilio vacia.
        """
        mesa = self._mesas.obtener_por_id(id)
        if not mesa:
            raise ValueError(f"Mesa inexistente: {id}")
        if mesa["estado"] != "DISPONIBLE":
            raise ValueError(
                f"No se puede abrir la mesa {id}: ya esta ocupada "
                f"(venta activa id={mesa.get('venta_activa_id')})"
            )
        es_domicilio = (mesa.get("tipo") or "MESA") == "DOMICILIO"
        cliente = (cliente or "").strip()
        direccion = (direccion or "").strip()
        if es_domicilio:
            if not cliente:
                raise ValueError(
                    "Los pedidos de domicilio requieren el nombre del cliente."
                )
            # La dirección es opcional para domicilios cercanos
        uid = usuario_id if usuario_id else (
            self._auth.usuario_actual.id if self._auth and self._auth.usuario_actual else None
        )
        if uid is None:
            raise PermissionError("Debe haber un usuario logueado para abrir una mesa.")
        self._requerir(Permisos.USAR_MESAS)
        venta_id = self._ventas.abrir_venta(id, uid, caja_id=None)
        if es_domicilio:
            self._db.execute(
                "UPDATE ventas SET cliente=?, direccion_entrega=? WHERE id=?;",
                (cliente, direccion, venta_id),
            )
            self._db.commit()
        self._mesas.ocupar(id, venta_id)
        if es_domicilio:
            self._asegurar_domicilio_disponible()
        return venta_id

    def _asegurar_domicilio_disponible(self):
        """Si ya no queda ninguna mesa de domicilio libre, crea una nueva (operación atómica)."""
        # Usar transacción para evitar race condition TOCTOU (Time Of Check, Time Of Use)
        with self._db.transaccion():
            if not self._mesas.hay_domicilio_disponible():
                self._mesas.crear_domicilio_automatico()

    def actualizar_datos_entrega(self, venta_id: int,
                                 cliente: Optional[str] = None,
                                 direccion: Optional[str] = None) -> bool:
        """Completa o corrige cliente/direccion de un pedido de domicilio."""
        self._requerir(Permisos.USAR_MESAS)
        venta = self._db.fetchone(
            "SELECT estado FROM ventas WHERE id=?;", (venta_id,)
        )
        if not venta or venta["estado"] != "ABIERTA":
            raise ValueError("Solo se pueden editar pedidos abiertos.")
        if cliente is not None:
            self._db.execute(
                "UPDATE ventas SET cliente=? WHERE id=?;",
                (cliente.strip(), venta_id),
            )
        if direccion is not None:
            self._db.execute(
                "UPDATE ventas SET direccion_entrega=? WHERE id=?;",
                (direccion.strip(), venta_id),
            )
        self._db.commit()
        return True

    def cerrar_mesa(self, id: int, caja_id: Optional[int] = None) -> Optional[int]:
        """
        Cierra la mesa SIN cobrar: anula el pedido abierto (la venta no se borra,
        cambia a estado ANULADA para conservar el historial) y libera la mesa.
        El cobro real es responsabilidad del Punto 5.
        """
        self._requerir(Permisos.USAR_MESAS)
        mesa = self._mesas.obtener_por_id(id)
        if not mesa:
            raise ValueError(f"No hay venta abierta en la mesa {id}")
        
        # Migración V6: venta_activa_id column removed. Get venta_id via LEFT JOIN
        venta = self._db.fetchone(
            "SELECT id FROM ventas WHERE mesa_id=? AND estado='ABIERTA';",
            (id,)
        )
        if not venta:
            raise ValueError(f"No hay venta abierta en la mesa {id}")
        
        venta_id = venta["id"]
        self._ventas.anular(venta_id)
        self._mesas.liberar(id)
        return venta_id

    def cancelar_pedido(self, id: int) -> bool:
        """
        Anula el pedido de una mesa y la deja DISPONIBLE.
        La venta NO se borra: queda con estado ANULADA (historial protegido).
        """
        return self.anular_pedido(id)

    def anular_pedido(self, id: int) -> bool:
        """
        Anula la venta abierta de una mesa (si existe) SIN borrarla,
        y libera la mesa de un golpe. Retorna True si se anulo.
        """
        self._requerir(Permisos.USAR_MESAS)
        mesa = self._mesas.obtener_por_id(id)
        if not mesa:
            return False
        
        # Migración V6: venta_activa_id column removed. Get venta_id via query
        venta = self._db.fetchone(
            "SELECT id FROM ventas WHERE mesa_id=? AND estado='ABIERTA';",
            (id,)
        )
        if not venta:
            return False
        
        venta_id = venta["id"]
        ok = self._ventas.anular(venta_id)
        # Liberar mesa siempre para que vuelva a DISPONIBLE
        try:
            self._mesas.liberar(id)
            
            # Si es un domicilio, limpiar los domicilios vacíos después de liberar
            es_domicilio = (mesa.get("tipo") or "MESA") == "DOMICILIO"
            if es_domicilio:
                self._mesas._limpiar_domicilios_vacios()
        except Exception:
            pass
        return ok

    # ---- Pedido ----
    def catalogo_productos(self, solo_activos=True):
        q = self._productos.listar_todos if not solo_activos else self._productos.listar_activos
        return q()

    def agregar_producto(self, venta_id: int, producto_id: int, cantidad: float = 1.0):
        """Agrega (o incrementa) un producto al pedido."""
        prod = self._productos.obtener_por_id(producto_id)
        if not prod:
            raise ValueError(f"Producto inexistente: {producto_id}")
        if prod["activo"] == 0:
            raise ValueError(f"Producto inactivo: {producto_id}")
        self._requerir(Permisos.USAR_MESAS)
        return self._ventas.agregar_detalle(
            venta_id, producto_id, prod["nombre"], cantidad, prod["precio"]
        )

    def modificar_cantidad(self, venta_id: int, detalle_id: int, cantidad: float):
        self._requerir(Permisos.USAR_MESAS)
        self._ventas.actualizar_cantidad_detalle(detalle_id, cantidad)

    def quitar_producto(self, venta_id: int, detalle_id: int):
        self._requerir(Permisos.USAR_MESAS)
        self._ventas.eliminar_detalle(detalle_id)

    # resultados / ui
    def detalles_pedido(self, venta_id: int):
        return self._ventas.obtener_detalles(venta_id)

    def resumen_pedido(self, venta_id: int):
        v = self._ventas.obtener_por_id(venta_id)
        if not v:
            return {}
        detalles = self.detalles_pedido(venta_id)
        total_items = round(sum(d["cantidad"] for d in detalles), 2)
        return {
            "venta": v,
            "detalles": detalles,
            "subtotal": round(v["subtotal"], 2),
            "total": round(v["total"], 2),
            "n_items": int(total_items),
        }

    def datos_mesa_activa(self, id: int):
        return self._mesas.obtener_por_id(id)
