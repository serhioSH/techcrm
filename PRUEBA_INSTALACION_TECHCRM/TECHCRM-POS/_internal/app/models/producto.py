# ============================================================
#  app/models/producto.py
# ============================================================
from dataclasses import dataclass
from typing import Optional


@dataclass
class Producto:
    id: Optional[int]
    nombre: str
    descripcion: Optional[str]
    categoria_id: Optional[int]
    precio: float
    activo: int = 1
    fecha_creacion: Optional[str] = None
    fecha_modificacion: Optional[str] = None
    # Campo auxiliar: nombre de la categoria (JOIN)
    categoria_nombre: Optional[str] = None
