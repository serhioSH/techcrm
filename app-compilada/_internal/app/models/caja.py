# ============================================================
#  app/models/caja.py
# ============================================================
from dataclasses import dataclass
from typing import Optional


@dataclass
class Caja:
    id: Optional[int]
    usuario_id: int
    fecha_apertura: Optional[str]
    monto_inicial: float = 0.0
    fecha_cierre: Optional[str] = None
    efectivo_esperado: Optional[float] = None
    efectivo_contado: Optional[float] = None
    diferencia: Optional[float] = None
    total_efectivo: float = 0.0
    total_transferencia: float = 0.0
    total_general: float = 0.0
    observaciones: Optional[str] = None
    estado: str = "ABIERTA"   # 'ABIERTA' | 'CERRADA'
    # Auxiliar
    usuario_nombre: Optional[str] = None
