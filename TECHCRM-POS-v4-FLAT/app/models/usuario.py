# ============================================================
#  app/models/usuario.py
# ============================================================
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Usuario:
    id: Optional[int]
    nombre: str
    usuario: str
    password_hash: str
    rol: str                      # 'ADMIN' | 'CAJERO'
    activo: int = 1
    fecha_creacion: Optional[str] = None

    def es_admin(self) -> bool:
        return self.rol == "ADMIN"

    def es_cajero(self) -> bool:
        return self.rol == "CAJERO"

    def esta_activo(self) -> bool:
        return self.activo == 1
