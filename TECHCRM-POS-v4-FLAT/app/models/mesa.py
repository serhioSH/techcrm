# ============================================================
#  app/models/mesa.py
# ============================================================
from dataclasses import dataclass
from typing import Optional


@dataclass
class Mesa:
    id: Optional[int]
    nombre: str
    estado: str = "DISPONIBLE"    # 'DISPONIBLE' | 'OCUPADA'
    # Migración V6: venta_activa_id removed from schema
    # Use LEFT JOIN on ventas table with estado='ABIERTA' to get active venta
    venta_activa_id: Optional[int] = None  # Kept for backward compat, populated by JOIN query

    def esta_disponible(self) -> bool:
        return self.estado == "DISPONIBLE"

    def esta_ocupada(self) -> bool:
        return self.estado == "OCUPADA"
