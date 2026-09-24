# ============================================================
#  app/services/caja_service.py
#  Gestion de apertura/cierre de caja por jornada
# ============================================================
from typing import Optional, List
from app.database.connection import DatabaseConnection
from app.services.permisos import Permisos, ServicioProtegido


class CajaService(ServicioProtegido):
    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth

    def caja_abierta(self) -> Optional[dict]:
        """Retorna la caja actualmente abierta, o None."""
        return self._db.fetchone(
            """SELECT c.*, u.nombre AS usuario_nombre
               FROM cajas c
               JOIN usuarios u ON c.usuario_id = u.id
               WHERE c.estado = 'ABIERTA'
               ORDER BY c.fecha_apertura DESC
               LIMIT 1;"""
        )

    def abrir(self, usuario_id: int, monto_inicial: float) -> int:
        self._requerir(Permisos.ABRIR_CERRAR_CAJA)
        c = self._db.execute(
            "INSERT INTO cajas (usuario_id, monto_inicial) VALUES (?,?);",
            (usuario_id, monto_inicial),
        )
        self._db.commit()
        return c.lastrowid

    def cerrar(self, caja_id: int, efectivo_contado: float, observaciones: str = "") -> dict:
        """Calcula diferencias y cierra la caja. Retorna el resumen."""
        self._requerir(Permisos.ABRIR_CERRAR_CAJA)
        resumen = self._calcular_resumen(caja_id)
        efectivo_esperado = resumen["efectivo_esperado"]
        # Signo segun PROYECTO.md: diferencia = esperado - contado
        # (positivo = faltante, negativo = sobrante)
        diferencia = round(efectivo_esperado - efectivo_contado, 2)

        self._db.execute(
            """UPDATE cajas
               SET fecha_cierre=datetime('now','localtime'),
                   efectivo_esperado=?,
                   efectivo_contado=?,
                   diferencia=?,
                   total_efectivo=?,
                   total_transferencia=?,
                   total_general=?,
                   observaciones=?,
                   estado='CERRADA'
               WHERE id=?;""",
            (
                efectivo_esperado,
                efectivo_contado,
                diferencia,
                resumen["total_efectivo"],
                resumen["total_transferencia"],
                resumen["total_general"],
                observaciones,
                caja_id,
            ),
        )
        self._db.commit()
        return {**resumen, "efectivo_contado": efectivo_contado, "diferencia": diferencia}

    def _calcular_resumen(self, caja_id: int) -> dict:
        caja = self._db.fetchone("SELECT monto_inicial FROM cajas WHERE id=?;", (caja_id,))
        monto_inicial = caja["monto_inicial"] if caja else 0

        # Usar las nuevas columnas efectivo_pago y transferencia_pago si existen
        # Si no existen (BD vieja), usar metodo_pago para compatibilidad
        try:
            totales = self._db.fetchone(
                """SELECT
                       COALESCE(SUM(efectivo_pago), 0) AS ef,
                       COALESCE(SUM(transferencia_pago), 0) AS tr,
                       COALESCE(SUM(total), 0) AS gen
                   FROM ventas
                   WHERE caja_id=? AND estado='CERRADA';""",
                (caja_id,),
            )
        except Exception:
            # Fallback para BD vieja sin efectivo_pago/transferencia_pago
            totales = self._db.fetchone(
                """SELECT
                       COALESCE(SUM(CASE WHEN metodo_pago='EFECTIVO'      THEN total ELSE 0 END),0) AS ef,
                       COALESCE(SUM(CASE WHEN metodo_pago='TRANSFERENCIA' THEN total ELSE 0 END),0) AS tr,
                       COALESCE(SUM(total), 0) AS gen
                   FROM ventas
                   WHERE caja_id=? AND estado='CERRADA';""",
                (caja_id,),
            )
        
        total_ef = round(totales["ef"], 2)
        total_tr = round(totales["tr"], 2)
        total_gen = round(totales["gen"], 2)
        efectivo_esperado = round(monto_inicial + total_ef, 2)

        return {
            "monto_inicial":        monto_inicial,
            "total_efectivo":       total_ef,
            "total_transferencia":  total_tr,
            "total_general":        total_gen,
            "efectivo_esperado":    efectivo_esperado,
        }

    def actualizar_totales(self, caja_id: int):
        """Recalcula y guarda los totales en tiempo real (para mostrar en pantalla)."""
        resumen = self._calcular_resumen(caja_id)
        self._db.execute(
            """UPDATE cajas
               SET total_efectivo=?, total_transferencia=?, total_general=?
               WHERE id=?;""",
            (resumen["total_efectivo"], resumen["total_transferencia"],
             resumen["total_general"], caja_id),
        )
        self._db.commit()
        return resumen

    def historial(self) -> List[dict]:
        self._requerir(Permisos.CONSULTAR_CIERRES_CAJA)
        return self._db.fetchall(
            """SELECT c.*, u.nombre AS usuario_nombre
               FROM cajas c
               JOIN usuarios u ON c.usuario_id = u.id
               ORDER BY c.fecha_apertura DESC;"""
        )
