# ============================================================
#  app/services/comprobante_service.py
#  Generacion de texto de comprobante para impresion termica
# ============================================================
from typing import Optional
from app.database.connection import DatabaseConnection
from app.services.configuracion_service import ConfiguracionService


def _acortar(texto: str, ancho: int) -> str:
    """Recorta una linea para que nunca exceda el ancho del papel."""
    texto = texto or ""
    if len(texto) <= ancho:
        return texto
    return texto[: max(1, ancho - 3)] + "..."



class ComprobanteService:
    def __init__(self, db: DatabaseConnection):
        self._db = db
        self._cfg = ConfiguracionService(db)

    def generar_texto(self, venta_id: int) -> str:
        """
        Genera el texto formateado del comprobante para impresora termica.
        El ancho se toma de la configuracion (58mm=32 chars, 80mm=48 chars).
        """
        ancho_mm = self._cfg.get("ancho_ticket_mm", "80")
        ancho = 32 if ancho_mm == "58" else 48

        venta = self._db.fetchone(
            """SELECT v.*, m.nombre AS mesa_nombre, u.nombre AS cajero_nombre
               FROM ventas v
               LEFT JOIN mesas m ON v.mesa_id = m.id
               LEFT JOIN usuarios u ON v.usuario_id = u.id
               WHERE v.id=?;""",
            (venta_id,),
        )
        if not venta:
            return "ERROR: Venta no encontrada."

        detalles = self._db.fetchall(
            "SELECT * FROM detalle_ventas WHERE venta_id=? ORDER BY id;",
            (venta_id,),
        )

        sep = "-" * ancho
        lineas = []

        # Encabezado
        nombre_neg = self._cfg.get("nombre_negocio", "Mi Negocio")
        lineas.append(nombre_neg.center(ancho))
        dir_neg = self._cfg.get("direccion", "")
        if dir_neg:
            lineas.append(dir_neg.center(ancho))
        tel = self._cfg.get("telefono", "")
        if tel:
            lineas.append(f"Tel: {tel}".center(ancho))
        lineas.append(sep)

        # Datos del comprobante
        lineas.append(f"Comprobante: #{venta['consecutivo']}")
        fecha_hora = venta["fecha_hora"] or ""
        partes = fecha_hora.split(" ")
        lineas.append(f"Fecha: {partes[0] if partes else '-'}")
        lineas.append(f"Hora:  {partes[1] if len(partes)>1 else '-'}")
        lineas.append(f"Mesa:  {venta['mesa_nombre'] or '-'}")
        lineas.append(f"Cajero:{venta['cajero_nombre'] or '-'}")
        cliente = (venta.get("cliente") or "").strip()
        if cliente:
            lineas.append(f"Cliente: {cliente}")
        direccion = (venta.get("direccion_entrega") or "").strip()
        if direccion:
            lineas.append(f"Entrega: {direccion}")
        lineas.append(sep)

        # Productos
        # (col + 1 + 4 + 1 + 6 + 1 + 6) = ancho  ->  col = ancho - 19
        col_nombre = ancho - 19
        lineas.append(f"{'Producto':<{col_nombre}} {'Cant':>4} {'Precio':>6} {'Sub':>6}")
        lineas.append(sep)
        for d in detalles:
            nombre = d["nombre_producto"][:col_nombre]
            lineas.append(
                f"{nombre:<{col_nombre}} {d['cantidad']:>4.0f} "
                f"{d['precio_unitario']:>6.0f} {d['subtotal']:>6.0f}"
            )
        lineas.append(sep)
        # (ancho-13) + 1 + 2 + 10 = ancho
        lineas.append(f"{'TOTAL':>{ancho-13}} $ {venta['total']:>10.0f}")
        lineas.append(f"{'Pago:':>{ancho-12}} {venta['metodo_pago'] or '-':>10}")
        lineas.append(sep)

        # Mensaje final
        msg = self._cfg.get("mensaje_final", "Gracias por su visita!")
        lineas.append(msg.center(ancho))
        lineas.append("")
        lineas.append("")

        return "\n".join(_acortar(linea, ancho) for linea in lineas)
