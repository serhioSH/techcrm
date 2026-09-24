# ============================================================
#  app/services/permisos.py
#  Matriz de permisos por rol — UNICA fuente de verdad.
#  Implementa el Punto 3: separacion real de permisos entre
#  ADMIN y CAJERO en la capa de logica (no solo en la UI).
# ============================================================


class Permisos:
    """Constantes de permisos (capacidades) del sistema."""

    # ---- Productos ----
    VER_PRODUCTOS          = "ver_productos"
    ADMINISTRAR_PRODUCTOS  = "administrar_productos"   # crear/editar/precio/estado

    # ---- Mesas ----
    USAR_MESAS             = "usar_mesas"              # abrir mesa, tomar/modificar pedido
    ADMINISTRAR_MESAS      = "administrar_mesas"       # crear/editar/eliminar mesas

    # ---- Usuarios ----
    ADMINISTRAR_USUARIOS   = "administrar_usuarios"

    # ---- Ventas ----
    COBRAR                 = "cobrar"
    ANULAR_VENTA_ABIERTA   = "anular_venta_abierta"    # pedido aun no cobrado
    ANULAR_VENTA_CERRADA   = "anular_venta_cerrada"    # comprobante historico (ADMIN)

    # ---- Caja ----
    ABRIR_CERRAR_CAJA      = "abrir_cerrar_caja"
    CONSULTAR_CIERRES_CAJA = "consultar_cierres_caja"

    # ---- Historial / comprobantes ----
    CONSULTAR_VENTAS           = "consultar_ventas"            # todas
    CONSULTAR_VENTAS_PROPIAS   = "consultar_ventas_propias"    # solo las propias
    REIMPRIMIR_COMPROBANTES    = "reimprimir_comprobantes"

    # ---- Reportes ----
    CONSULTAR_REPORTES     = "consultar_reportes"
    EXPORTAR_EXCEL         = "exportar_excel"

    # ---- Sistema ----
    MODIFICAR_CONFIGURACION = "modificar_configuracion"
    REALIZAR_BACKUP         = "realizar_backup"
    ADMINISTRAR_SISTEMA     = "administrar_sistema"  # GitHub, Reiniciar BD (solo TECNICO)


ROLES_VALIDOS = ("ADMIN", "CAJERO", "TECNICO")

# ------------------------------------------------------------
# ADMIN: dueño del negocio - operaciones del negocio (NO sistema)
# ------------------------------------------------------------
_PERMISOS_ADMIN = [
    Permisos.VER_PRODUCTOS,
    Permisos.ADMINISTRAR_PRODUCTOS,
    Permisos.USAR_MESAS,
    Permisos.ADMINISTRAR_MESAS,
    Permisos.ADMINISTRAR_USUARIOS,
    Permisos.COBRAR,
    Permisos.ANULAR_VENTA_ABIERTA,
    Permisos.ANULAR_VENTA_CERRADA,
    Permisos.ABRIR_CERRAR_CAJA,
    Permisos.CONSULTAR_CIERRES_CAJA,
    Permisos.CONSULTAR_VENTAS,
    Permisos.CONSULTAR_VENTAS_PROPIAS,
    Permisos.REIMPRIMIR_COMPROBANTES,
    Permisos.CONSULTAR_REPORTES,
    Permisos.EXPORTAR_EXCEL,
    Permisos.MODIFICAR_CONFIGURACION,
    Permisos.REALIZAR_BACKUP,
]

# ------------------------------------------------------------
# CAJERO: iniciar sesion, consultar productos, abrir mesas,
# tomar/modificar pedidos, cobrar, elegir metodo de pago,
# imprimir comprobante, ver caja, ver reportes (sin exportar),
# reimpresion de comprobantes. NO puede: agregar productos,
# usuarios, config, ver cierres de caja, exportar Excel.
# ------------------------------------------------------------
_PERMISOS_CAJERO = [
    Permisos.VER_PRODUCTOS,
    Permisos.USAR_MESAS,
    Permisos.COBRAR,
    Permisos.ANULAR_VENTA_ABIERTA,
    Permisos.CONSULTAR_VENTAS_PROPIAS,
    Permisos.REIMPRIMIR_COMPROBANTES,
    Permisos.CONSULTAR_REPORTES,
]

# ------------------------------------------------------------
# TECNICO (CRMTECH): admin tecnico - administración del sistema
# Puede: ver/administrar productos, usuarios, mesas, config, backups, reportes, usar mesas
# + GitHub Config y Reiniciar BD (ADMINISTRAR_SISTEMA)
# NO puede: abrir/cerrar caja, ver cierres de caja, cobrar, anular ventas
# (operaciones del negocio son del ADMIN/Dueño)
# ------------------------------------------------------------
_PERMISOS_TECNICO = [
    Permisos.VER_PRODUCTOS,
    Permisos.ADMINISTRAR_PRODUCTOS,
    Permisos.USAR_MESAS,
    Permisos.ADMINISTRAR_MESAS,
    Permisos.ADMINISTRAR_USUARIOS,
    Permisos.MODIFICAR_CONFIGURACION,
    Permisos.REALIZAR_BACKUP,
    Permisos.CONSULTAR_REPORTES,
    Permisos.EXPORTAR_EXCEL,
    Permisos.CONSULTAR_VENTAS,
    Permisos.ADMINISTRAR_SISTEMA,  # GitHub Config + Reiniciar BD (solo TECNICO)
]

PERMISOS_POR_ROL = {
    "ADMIN":   tuple(_PERMISOS_ADMIN),
    "CAJERO":  tuple(_PERMISOS_CAJERO),
    "TECNICO": tuple(_PERMISOS_TECNICO),
}


def rol_valido(rol: str) -> bool:
    """True si el rol existe en el sistema."""
    return rol in ROLES_VALIDOS


def permisos_de(rol: str) -> tuple:
    """Retorna los permisos de un rol (tupla vacia si el rol no existe)."""
    return PERMISOS_POR_ROL.get(rol, ())


def puede(rol: str, permiso: str) -> bool:
    """True si el rol tiene el permiso."""
    return permiso in PERMISOS_POR_ROL.get(rol, ())


class ServicioProtegido:
    """
    Mixin para exigir permisos en la capa de logica de negocio.

    Los servicios que heredan reciben la sesion (AuthService) en su
    constructor y llaman a self._requerir(permiso) en cada operacion
    sensible:

    - auth con sesion activa  -> exige el permiso (PermissionError si falta).
    - auth sin usuario logueado -> niega todo (no autenticado).
    - auth=None               -> uso interno/pruebas de la capa de datos,
                                 donde no hay sesion que validar.
    """

    _auth = None

    def _requerir(self, permiso: str):
        if self._auth is None:
            return
        self._auth.requerir(permiso)
