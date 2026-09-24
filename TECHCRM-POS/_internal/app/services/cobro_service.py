# -*- coding: utf-8 -*-
#  app/services/cobro_service.py
#  Cobro, caja y comprobante fisico (Punto 5)
# ============================================================
from typing import Optional
from app.database.connection import DatabaseConnection
from app.services.permisos import Permisos, ServicioProtegido
from app.services.venta_service import VentaService
from app.services.caja_service import CajaService
from app.services.mesa_service import MesaService
from app.services.comprobante_service import ComprobanteService
from app.services.configuracion_service import ConfiguracionService
import os
from datetime import datetime

from app.utils.paths import COMPROBANTES_PATH


METODOS_PAGO = ("EFECTIVO", "TRANSFERENCIA")


class CobroService(ServicioProtegido):
    """
    Flujo completo de cobro de una venta abierta:
    valida, registra el pago, actualiza la caja, genera el comprobante,
    libera la mesa y devuelve el resumen (incluido el cambio).

    Reglas del Punto 5:
    - Debe existir una caja ABIERTA para poder cobrar.
    - Las TRANSFERENCIAS no suman al efectivo fisico de la caja.
    - No se permiten ventas duplicadas (cobro idempotente).
    """

    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth
        self._ventas = VentaService(db, auth)
        self._cajas = CajaService(db, auth)
        self._mesas = MesaService(db, auth)
        self._comprobantes = ComprobanteService(db)
        self._config = ConfiguracionService(db, auth)

    # ------------------------------------------------------
    # Consultas previas (sin efectos)
    # ------------------------------------------------------
    def caja_abierta(self) -> Optional[dict]:
        return self._cajas.caja_abierta()

    def venta_cobrable(self, venta_id: int) -> dict:
        """Valida que la venta exista, este ABIERTA y tenga productos."""
        venta = self._db.fetchone(
            """SELECT v.*, m.nombre AS mesa_nombre,
                      m.tipo AS mesa_tipo
               FROM ventas v
               LEFT JOIN mesas m ON v.mesa_id = m.id
               WHERE v.id = ?;""",
            (venta_id,),
        )
        if not venta:
            raise ValueError("La venta no existe.")
        if venta["estado"] != "ABIERTA" or venta["cobro_procesado"] == 1:
            raise ValueError("Esta venta ya fue cobrada o anulada.")
        if float(venta["total"] or 0) <= 0:
            raise ValueError("El pedido no tiene productos para cobrar.")
        return venta

    @staticmethod
    def calcular_cambio(total: float, recibido: float) -> float:
        return round(float(recibido) - float(total), 2)

    def resumen_cobro(self, venta_id: int) -> dict:
        """Datos que necesita la pantalla de cobro."""
        venta = self.venta_cobrable(venta_id)
        return {
            "venta_id": venta_id,
            "consecutivo": venta["consecutivo"],
            "mesa_nombre": venta["mesa_nombre"] or "-",
            "mesa_tipo": venta.get("mesa_tipo") or "MESA",
            "cliente": (venta.get("cliente") or "").strip(),
            "direccion": (venta.get("direccion_entrega") or "").strip(),
            "subtotal": round(float(venta["subtotal"] or 0), 2),
            "descuento": round(float(venta["descuento"] or 0), 2),
            "total": round(float(venta["total"] or 0), 2),
        }

    # ------------------------------------------------------
    # Cobro
    # ------------------------------------------------------
    def cobrar(self, venta_id: int, metodo_pago: str,
               recibido: Optional[float] = None,
               direccion: Optional[str] = None) -> dict:
        """
        Cobra una venta abierta. Es idempotente: si la venta ya fue cobrada
        lanza ValueError y NO duplica el registro.

        metodo_pago: 'EFECTIVO' | 'TRANSFERENCIA'
        recibido: obligatorio en EFECTIVO (se calcula el cambio).
        """
        self._requerir(Permisos.COBRAR)
        metodo_pago = (metodo_pago or "").strip().upper()
        if metodo_pago not in METODOS_PAGO:
            raise ValueError("Metodo de pago invalido: use EFECTIVO o TRANSFERENCIA.")

        if direccion is not None:
            self._db.execute(
                "UPDATE ventas SET direccion_entrega=? WHERE id=?;",
                (direccion.strip(), venta_id),
            )
            self._db.commit()

        venta = self.venta_cobrable(venta_id)
        total = round(float(venta["total"] or 0), 2)

        caja = self._cajas.caja_abierta()
        if caja is None:
            raise ValueError("Debe abrir la caja antes de cobrar.")

        recibido_num = None
        cambio = None
        if metodo_pago == "EFECTIVO":
            if recibido is None:
                raise ValueError("Ingrese el valor recibido en efectivo.")
            try:
                recibido_num = round(float(recibido), 2)
            except (TypeError, ValueError):
                raise ValueError("El valor recibido no es valido.")
            if recibido_num < total:
                raise ValueError(
                    f"El valor recibido no alcanza el total ({total:,.0f})."
                )
            cambio = self.calcular_cambio(total, recibido_num)

        # Registro atomico: solo una operacion puede cerrar la venta
        with self._db.transaccion():
            cursor = self._db.execute(
                """UPDATE ventas
                      SET estado='CERRADA', metodo_pago=?, cobro_procesado=1,
                          caja_id=?, fecha_hora=datetime('now','localtime')
                    WHERE id=? AND estado='ABIERTA' AND cobro_procesado=0;""",
                (metodo_pago, caja["id"], venta_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Esta venta ya fue cobrada.")

        # Totales de la jornada (la transferencia NO suma al efectivo fisico)
        self._cajas.actualizar_totales(caja["id"])

        # La mesa vuelve a DISPONIBLE
        if venta["mesa_id"] is not None:
            self._mesas.liberar(venta["mesa_id"])
            
            # Si es un domicilio, limpiar los domicilios vacíos después de liberar
            if venta["mesa_tipo"] == "DOMICILIO":
                self._mesas._limpiar_domicilios_vacios()

        # Comprobante: texto + archivo fisico independiente
        texto = self._comprobantes.generar_texto(venta_id)
        ruta = self._guardar_comprobante(venta_id, texto)

        return {
            "venta_id": venta_id,
            "consecutivo": venta["consecutivo"],
            "mesa_nombre": venta["mesa_nombre"] or "-",
            "total": total,
            "metodo_pago": metodo_pago,
            "recibido": recibido_num,
            "cambio": cambio,
            "caja_id": caja["id"],
            "comprobante_texto": texto,
            "comprobante_ruta": ruta,
        }

    def cobrar_efectivo(self, venta_id: int, recibido: float,
                        direccion: Optional[str] = None) -> dict:
        return self.cobrar(venta_id, "EFECTIVO", recibido, direccion)

    def cobrar_transferencia(self, venta_id: int,
                             direccion: Optional[str] = None) -> dict:
        return self.cobrar(venta_id, "TRANSFERENCIA", None, direccion)

    def cobrar_mixto(self, venta_id: int, efectivo: float, transferencia: float,
                     direccion: Optional[str] = None) -> dict:
        """Cobra una venta con pago mixto (efectivo + transferencia).
        
        Registra como EFECTIVO pero suma el transferencia a la caja de transferencias.
        Así el sistema distingue correctamente qué parte es cada una.
        """
        self._requerir(Permisos.COBRAR)
        
        if direccion is not None:
            self._db.execute(
                "UPDATE ventas SET direccion_entrega=? WHERE id=?;",
                (direccion.strip(), venta_id),
            )
            self._db.commit()

        venta = self.venta_cobrable(venta_id)
        total = round(float(venta["total"] or 0), 2)

        # Validar que la suma de efectivo + transferencia = total
        if abs(efectivo + transferencia - total) > 0.01:
            raise ValueError(f"La suma de efectivo + transferencia debe ser {total:,.0f}")

        caja = self._cajas.caja_abierta()
        if caja is None:
            raise ValueError("Debe abrir la caja antes de cobrar.")

        # Registrar como EFECTIVO en la venta (para historiales)
        with self._db.transaccion():
            cursor = self._db.execute(
                """UPDATE ventas
                      SET estado='CERRADA', metodo_pago='EFECTIVO', cobro_procesado=1,
                          caja_id=?, fecha_hora=datetime('now','localtime')
                    WHERE id=? AND estado='ABIERTA' AND cobro_procesado=0;""",
                (caja["id"], venta_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("Esta venta ya fue cobrada.")

        # Actualizar totales de caja
        # Nota: sumamos efectivo a total_efectivo, transferencia a total_transferencia
        self._db.execute(
            """UPDATE cajas 
               SET total_efectivo = total_efectivo + ?,
                   total_transferencia = total_transferencia + ?
               WHERE id = ?;""",
            (round(efectivo, 2), round(transferencia, 2), caja["id"]),
        )
        self._db.commit()

        # La mesa vuelve a DISPONIBLE
        if venta["mesa_id"] is not None:
            self._mesas.liberar(venta["mesa_id"])

        # Comprobante
        texto = self._comprobantes.generar_texto(venta_id)
        ruta = self._guardar_comprobante(venta_id, texto)

        return {
            "venta_id": venta_id,
            "consecutivo": venta["consecutivo"],
            "mesa_nombre": venta["mesa_nombre"] or "-",
            "total": total,
            "metodo_pago": "MIXTO",
            "efectivo_pago": round(efectivo, 2),
            "transferencia_pago": round(transferencia, 2),
            "recibido": round(efectivo, 2),
            "cambio": 0,
            "caja_id": caja["id"],
            "comprobante_texto": texto,
            "comprobante_ruta": ruta,
        }

    # ------------------------------------------------------
    # Comprobante
    # ------------------------------------------------------
    def _guardar_comprobante(self, venta_id: int, texto: str) -> str:
        """Guarda el comprobante como archivo independiente en comprobantes/."""
        os.makedirs(COMPROBANTES_PATH, exist_ok=True)
        fila = self._db.fetchone(
            "SELECT consecutivo FROM ventas WHERE id=?;", (venta_id,)
        )
        consecutivo = fila["consecutivo"] if fila else venta_id
        marca = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre = f"comprobante_{consecutivo:06d}_{marca}.txt"
        ruta = os.path.join(COMPROBANTES_PATH, nombre)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(texto)
        return ruta

    def comprobante_texto(self, venta_id: int) -> str:
        return self._comprobantes.generar_texto(venta_id)

    def imprimir_comprobante(self, venta_id: int) -> tuple:
        """
        Imprime en la impresora configurada. Retorna (ok, mensaje).
        Si no hay impresora configurada no falla: el comprobante ya quedo
        guardado como archivo (la integracion fina es del Punto 6).
        """
        self._requerir(Permisos.COBRAR)
        impresora = (self._config.get("impresora", "") or "").strip()
        if not impresora:
            return False, "No hay impresora configurada (comprobante guardado en archivo)."
        from app.printing.printer_manager import PrinterManager
        from app.printing import escpos
        texto = self._comprobantes.generar_texto(venta_id)
        logo = (self._config.get("logo_path", "") or "").strip()
        ancho = self._config.get("ancho_ticket_mm", "80")
        datos = escpos.construir_ticket(
            texto, logo if logo else None, ancho
        )
        try:
            ok = PrinterManager.imprimir_bytes(datos, impresora)
        except Exception as e:
            return False, f"Error al imprimir: {e}"
        if ok:
            return True, "Comprobante enviado a la impresora."
        try:
            ok = PrinterManager.imprimir_texto(texto, impresora)
        except Exception as e:
            return False, f"Error al imprimir: {e}"
        if ok:
            return True, "Comprobante enviado (sin logo)."
        return False, "No se pudo imprimir el comprobante."

