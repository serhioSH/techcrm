# ============================================================
#  app/services/auth_service.py
#  Autenticacion, hashing de contrasenas y control de acceso
# ============================================================
import bcrypt
from typing import Optional
from app.database.connection import DatabaseConnection
from app.models.usuario import Usuario
from app.services.permisos import permisos_de


class AuthService:
    """Servicio de autenticacion y gestion de sesion."""

    def __init__(self, db: DatabaseConnection):
        self._db = db
        self._usuario_actual: Optional[Usuario] = None

    # ----------------------------------------------------------
    # Autenticacion
    # ----------------------------------------------------------
    def login(self, usuario: str, password: str) -> Optional[Usuario]:
        """
        Verifica credenciales. Retorna el Usuario si son correctas,
        None en caso contrario.
        """
        row = self._db.fetchone(
            "SELECT * FROM usuarios WHERE usuario = ? AND activo = 1;",
            (usuario,),
        )
        if not row:
            return None

        hash_almacenado = row["password_hash"].encode()
        if not bcrypt.checkpw(password.encode(), hash_almacenado):
            return None

        self._usuario_actual = Usuario(**{
            k: row[k] for k in
            ["id","nombre","usuario","password_hash","rol","activo","fecha_creacion"]
        })
        return self._usuario_actual

    def logout(self):
        """Cierra la sesion actual."""
        self._usuario_actual = None

    @property
    def usuario_actual(self) -> Optional[Usuario]:
        return self._usuario_actual

    def esta_autenticado(self) -> bool:
        return self._usuario_actual is not None
    def puede(self, permiso: str) -> bool:
        """True si el usuario actual tiene el permiso indicado."""
        if self._usuario_actual is None:
            return False
        return permiso in permisos_de(self._usuario_actual.rol)

    def requiere(self, permiso: str) -> bool:
        """
        Exige el permiso en la capa de logica (Punto 3).
        Lanza PermissionError si no hay sesion o el rol no tiene el permiso.
        """
        if self._usuario_actual is None:
            raise PermissionError(
                "Debe iniciar sesion para realizar esta operacion."
            )
        if not self.puede(permiso):
            raise PermissionError(
                f"El rol {self._usuario_actual.rol} no tiene el permiso '{permiso}'."
            )
        return True


    # ----------------------------------------------------------

    def requerir(self, permiso: str) -> bool:
        """Alias de requiere() para uso desde los servicios protegidos."""
        return self.requiere(permiso)

    # Control de permisos
    # ----------------------------------------------------------
    def requiere_admin(self) -> bool:
        """Verifica que el usuario actual sea ADMIN."""
        return self._usuario_actual is not None and self._usuario_actual.es_admin()

    def puede_cobrar(self) -> bool:
        return self._usuario_actual is not None

    def puede_administrar(self) -> bool:
        return self.requiere_admin()

    # ----------------------------------------------------------
    # Utilidades de hash
    # ----------------------------------------------------------
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verificar_password(password: str, hash_almacenado: str) -> bool:
        return bcrypt.checkpw(password.encode(), hash_almacenado.encode())

    def registrar_usuario(self, nombre: str, usuario: str, password: str, rol: str = "CAJERO") -> bool:
        """
        Registra un nuevo usuario en el sistema.
        Retorna True si fue exitoso, False si el usuario ya existe.
        """
        # Verificar si el usuario ya existe
        existente = self._db.fetchone(
            "SELECT id FROM usuarios WHERE usuario = ?", (usuario,)
        )
        if existente:
            return False
        
        # Crear hash de la contraseña
        password_hash = self.hash_password(password)
        
        # Insertar nuevo usuario
        try:
            self._db.execute(
                """INSERT INTO usuarios (nombre, usuario, password_hash, rol, activo)
                   VALUES (?, ?, ?, ?, 1)""",
                (nombre, usuario, password_hash, rol)
            )
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            return False
