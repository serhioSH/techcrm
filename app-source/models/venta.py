# ============================================================
#  app/models/venta.py
# ============================================================
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class DetalleVenta:
    id: Optional[int]
    venta_id: Optional[int]
    producto_id: Optional[int]
    nombre_producto: str
    cantidad: float
    precio_unitario: float
    subtotal: float


@dataclass
class Venta:
    id: Optional[int]
    consecutivo: Optional[int]
    mesa_id: Optional[int]
    usuario_id: int
    caja_id: Optional[int]
    fecha_hora: Optional[str]
    subtotal: float = 0.0
    descuento: float = 0.0
    total: float = 0.0
    metodo_pago: Optional[str] = None   # 'EFECTIVO' | 'TRANSFERENCIA'
    estado: str = "ABIERTA"             # 'ABIERTA' | 'CERRADA' | 'ANULADA'
    cobro_procesado: int = 0
    # Campos auxiliares (no en DB directamente)
    detalles: List[DetalleVenta] = field(default_factory=list)
    mesa_nombre: Optional[str] = None
    usuario_nombre: Optional[str] = None
