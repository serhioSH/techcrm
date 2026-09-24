# ============================================================
#  app/services/usuario_service.py
#  CRUD de usuarios
# ============================================================
from typing import List, Optional
from app.database.connection import DatabaseConnection
from app.models.usuario import Usuario
from app.services.auth_service import AuthService
from app.services.permisos import Permisos, ServicioProtegido, rol_valido
from app.utils.validators import validar_password, validar_usuario


class UsuarioService(ServicioProtegido):
    def __init__(self, db: DatabaseConnection, auth=None):
        self._db = db
        self._auth = auth

    def listar(self) -> List[dict]:
        self._requerir(Permisos.ADMINISTRAR_USUARIOS)
        return self._db.fetchall(
            "SELECT id, nombre, usuario, rol, activo, fecha_creacion FROM usuarios ORDER BY nombre;"
        )

    def obtener_por_id(self, id: int) -> Optional[dict]:
        return self._db.fetchone("SELECT * FROM usuarios WHERE id = ?;", (id,))

    def crear(self, nombre: str, usuario: str, password: str, rol: str) -> int:
        self._requerir(Permisos.ADMINISTRAR_USUARIOS)
        ok, msg = validar_usuario(usuario)
        if not ok:
            raise ValueError(msg)
        ok, msg = validar_password(password)
        if not ok:
            raise ValueError(msg)
        if not rol_valido(rol):
            raise ValueError("El rol debe ser ADMIN o CAJERO.")
        hash_pwd = AuthService.hash_password(password)
        cursor = self._db.execute(
            "INSERT INTO usuarios (nombre, usuario, password_hash, rol) VALUES (?,?,?,?);",
            (nombre, usuario, hash_pwd, rol),
        )
        self._db.commit()
        return cursor.lastrowid

    def actualizar(self, id: int, nombre: str, usuario: str, rol: str):
        self._requerir(Permisos.ADMINISTRAR_USUARIOS)
        if not rol_valido(rol):
            raise ValueError("El rol debe ser ADMIN o CAJERO.")
        fila = self._db.fetchone("SELECT rol FROM usuarios WHERE id=?;", (id,))
        if fila and fila["rol"] == "ADMIN" and rol != "ADMIN":
            self._proteger_ultimo_admin(excluyendo_id=id)
        self._db.execute(
            "UPDATE usuarios SET nombre=?, usuario=?, rol=? WHERE id=?;",
            (nombre, usuario, rol, id),
        )
        self._db.commit()

    def cambiar_password(self, id: int, nueva_password: str):
        """
        Cambia la contrasena de un usuario. Cada uno puede cambiar la propia;
        la de otros usuarios solo la cambia un ADMIN.
        """
        propio = (
            self._auth is not None
            and self._auth.usuario_actual is not None
            and self._auth.usuario_actual.id == id
        )
        if not propio:
            self._requerir(Permisos.ADMINISTRAR_USUARIOS)
        ok, msg = validar_password(nueva_password)
        if not ok:
            raise ValueError(msg)
        hash_pwd = AuthService.hash_password(nueva_password)
        self._db.execute(
            "UPDATE usuarios SET password_hash=? WHERE id=?;",
            (hash_pwd, id),
        )
        self._db.commit()

    def cambiar_estado(self, id: int, activo: bool):
        self._requerir(Permisos.ADMINISTRAR_USUARIOS)
        if not activo:
            fila = self._db.fetchone(
                "SELECT rol, activo FROM usuarios WHERE id=?;", (id,)
            )
            if fila and fila["rol"] == "ADMIN" and fila["activo"] == 1:
                self._proteger_ultimo_admin(excluyendo_id=id)
        self._db.execute(
            "UPDATE usuarios SET activo=? WHERE id=?;",
            (1 if activo else 0, id),
        )
        self._db.commit()

    def _proteger_ultimo_admin(self, excluyendo_id: Optional[int] = None):
        """Impide dejar al sistema sin ningun ADMIN activo."""
        if excluyendo_id is None:
            row = self._db.fetchone(
                "SELECT COUNT(*) AS n FROM usuarios WHERE rol='ADMIN' AND activo=1;"
            )
        else:
            row = self._db.fetchone(
                "SELECT COUNT(*) AS n FROM usuarios "
                "WHERE rol='ADMIN' AND activo=1 AND id != ?;",
                (excluyendo_id,),
            )
        if row and row["n"] == 0:
            raise ValueError("No se puede retirar al unico ADMIN activo del sistema.")

    def cambiar_mi_password(self, actual: str, nueva: str) -> bool:
        """Cambia la contrasena del usuario de la sesion actual, verificando la anterior."""
        if self._auth is None or self._auth.usuario_actual is None:
            raise PermissionError("Debe iniciar sesion para cambiar su contrasena.")
        user = self._auth.usuario_actual
        fila = self._db.fetchone(
            "SELECT password_hash FROM usuarios WHERE id=?;", (user.id,)
        )
        if not fila or not AuthService.verificar_password(
            actual, fila["password_hash"]
        ):
            raise ValueError("La contrasena actual es incorrecta.")
        ok, msg = validar_password(nueva)
        if not ok:
            raise ValueError(msg)
        self._db.execute(
            "UPDATE usuarios SET password_hash=? WHERE id=?;",
            (AuthService.hash_password(nueva), user.id),
        )
        self._db.commit()
        return True

    def existe_usuario(self, usuario: str, excluir_id: Optional[int] = None) -> bool:
        if excluir_id:
            row = self._db.fetchone(
                "SELECT id FROM usuarios WHERE usuario=? AND id!=?;",
                (usuario, excluir_id),
            )
        else:
            row = self._db.fetchone(
                "SELECT id FROM usuarios WHERE usuario=?;", (usuario,)
            )
        return row is not None
