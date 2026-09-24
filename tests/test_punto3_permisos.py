# ============================================================
#  tests/test_punto3_permisos.py
#  Pruebas del PUNTO 3 — Login, usuarios y permisos
#  Ejecutar desde la raiz:  python tests/test_punto3_permisos.py
#  No requiere PySide6: valida la capa de logica de negocio.
# ============================================================
import os
import sys
import shutil
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

# BD temporal ANTES de importar la capa de datos
_TMP = tempfile.mkdtemp(prefix="pos_test_p3_")
import app.utils.paths as paths
paths.DB_PATH = os.path.join(_TMP, "pos_test.db")

from app.database.connection import DatabaseConnection
from app.database.migrations import inicializar_base_de_datos
from app.database.seeder import ejecutar_seeder
from app.services.auth_service import AuthService
from app.services.permisos import Permisos, permisos_de, puede as puede_rol
from app.services.usuario_service import UsuarioService
from app.services.producto_service import ProductoService
from app.services.mesa_service import MesaService
from app.services.caja_service import CajaService
from app.services.venta_service import VentaService
from app.services.reporte_service import ReporteService
from app.services.backup_service import BackupService
from app.services.configuracion_service import ConfiguracionService

RESULTADOS = []
STATE = {}


def registrar(nombre, fn, db):
    try:
        fn(db)
        RESULTADOS.append((nombre, True, ""))
        print(f"  [ OK ] {nombre}")
    except AssertionError as e:
        RESULTADOS.append((nombre, False, str(e)))
        print(f"  [FALLA] {nombre} -> {e}")
    except Exception as e:
        RESULTADOS.append((nombre, False, f"{type(e).__name__}: {e}"))
        print(f"  [ERROR] {nombre} -> {type(e).__name__}: {e}")


def espera_permiso(fn):
    """Exige que fn() sea rechazado con PermissionError."""
    try:
        fn()
    except PermissionError:
        return
    raise AssertionError("La operacion debio ser denegada por permisos")

def t01_matriz_de_permisos(db):
    """La matriz debe reflejar el Punto 3 del PROYECTO.md."""
    admin, cajero = permisos_de("ADMIN"), permisos_de("CAJERO")
    # CAJERO puede: consultar productos, mesas/pedidos, cobrar, reportes, reimpresión, anular venta abierta, consultar ventas propias
    for p in (Permisos.VER_PRODUCTOS, Permisos.USAR_MESAS, Permisos.COBRAR, 
              Permisos.ANULAR_VENTA_ABIERTA, Permisos.CONSULTAR_VENTAS_PROPIAS,
              Permisos.REIMPRIMIR_COMPROBANTES, Permisos.CONSULTAR_REPORTES):
        assert p in cajero, f"CAJERO deberia poder: {p}"
    # CAJERO NO puede: precios, usuarios, config, historial completo,
    # cierres de caja, excel, backups, anular venta cerrada, admin mesas/productos
    for p in (Permisos.ADMINISTRAR_PRODUCTOS, Permisos.ADMINISTRAR_USUARIOS,
              Permisos.MODIFICAR_CONFIGURACION, Permisos.CONSULTAR_VENTAS,
              Permisos.CONSULTAR_CIERRES_CAJA, Permisos.EXPORTAR_EXCEL, 
              Permisos.REALIZAR_BACKUP, Permisos.ABRIR_CERRAR_CAJA, 
              Permisos.ANULAR_VENTA_CERRADA, Permisos.ADMINISTRAR_MESAS):
        assert p not in cajero, f"CAJERO NO deberia poder: {p}"
    # ADMIN puede todo lo del cajero + administracion
    for p in cajero:
        assert p in admin, f"ADMIN deberia heredar el permiso: {p}"
    for p in (Permisos.CONSULTAR_VENTAS, Permisos.REALIZAR_BACKUP,
              Permisos.MODIFICAR_CONFIGURACION, Permisos.ANULAR_VENTA_CERRADA):
        assert p in admin
    assert not puede_rol("INVENTADO", Permisos.COBRAR)


def t02_login_y_sesion(db):
    auth = AuthService(db)
    assert auth.usuario_actual is None
    assert auth.login("admin", "mala") is None
    assert auth.login("noexiste", "admin123") is None
    user = auth.login("admin", "admin123")
    assert user is not None and user.rol == "ADMIN"
    assert auth.esta_autenticado() and auth.usuario_actual.id == user.id
    STATE["admin_id"] = user.id
    # Logout cierra la sesion y todo queda denegado
    auth.logout()
    espera_permiso(lambda: auth.requiere(Permisos.COBRAR))
    STATE["auth"] = auth


def t03_crear_usuarios_del_rol(db):
    auth = STATE["auth"]
    assert auth.login("admin", "admin123")
    svc = UsuarioService(db, auth)
    # ADMIN crea CAJEROS y otro ADMIN
    STATE["cajero1_id"] = svc.crear("Cajero Uno", "cajero1", "clave123", "CAJERO")
    STATE["cajero2_id"] = svc.crear("Cajero Dos", "cajero2", "clave234", "CAJERO")
    STATE["admin2_id"] = svc.crear("Admin Dos", "admin2", "clave345", "ADMIN")
    # Usuario duplicado: rechazado por la BD
    try:
        svc.crear("Duplicado", "cajero1", "clave999", "CAJERO")
        raise AssertionError("Debio rechazar el usuario duplicado")
    except Exception as e:
        assert "UNIQUE" in str(e), f"Error inesperado: {e}"
    # Rol invalido: rechazado por validacion
    try:
        svc.crear("Raro", "usuario_raro", "clave999", "SUPERVISOR")
        raise AssertionError("Debio rechazar el rol invalido")
    except ValueError:
        pass
    # Contrasena corta: rechazada
    try:
        svc.crear("Corto", "usuario_corto", "abc", "CAJERO")
        raise AssertionError("Debio rechazar la contrasena corta")
    except ValueError:
        pass

def t04_cajero_sin_permisos_de_administracion(db):
    auth = STATE["auth"]
    auth.logout()
    assert auth.login("cajero1", "clave123")
    assert auth.usuario_actual.rol == "CAJERO"

    usuarios = UsuarioService(db, auth)
    productos = ProductoService(db, auth)
    mesas = MesaService(db, auth)
    caja = CajaService(db, auth)
    reportes = ReporteService(db, auth)
    backup = BackupService(db, auth)
    config = ConfiguracionService(db, auth)
    ventas = VentaService(db, auth)

    # NO puede: crear/modificar usuarios ni precios ni productos
    espera_permiso(lambda: usuarios.crear("X", "usuariox", "clave123", "ADMIN"))
    espera_permiso(lambda: usuarios.cambiar_estado(1, False))
    espera_permiso(lambda: productos.crear("Producto X", "", None, 1000))
    espera_permiso(lambda: productos.cambiar_precio(1, 5000))
    espera_permiso(lambda: productos.cambiar_estado(1, False))
    espera_permiso(lambda: mesas.crear("Mesa Fantasma"))
    espera_permiso(lambda: mesas.eliminar(1))
    # NO puede: abrir/cerrar caja ni ver cierres
    espera_permiso(lambda: caja.abrir(STATE["cajero1_id"], 10000))
    espera_permiso(lambda: caja.historial())
    # PUEDE: consultar reportes (NUEVO permiso para CAJERO)
    # PERO NO puede: excel, backups, configuracion
    espera_permiso(lambda: reportes.exportar_excel(
        "2026-01-01", "2026-12-31", os.path.join(_TMP, "r.xlsx")))
    espera_permiso(lambda: backup.crear_backup())
    espera_permiso(lambda: config.set("nombre_negocio", "Hack"))
    # NO puede: anular una venta CERRADA (historico) — cubierto en t07
    STATE["svc_cajero"] = (ventas, mesas, caja)


def t05_cajero_operaciones_de_su_rol(db):
    """El cajero SI puede: mesas, pedidos, cobrar y ver SUS ventas."""
    auth = STATE["auth"]
    ventas, mesas, caja = STATE["svc_cajero"]
    productos = ProductoService(db, auth)

    # Abrir caja como ADMIN para poder cobrar dentro de una jornada
    auth_admin = AuthService(db)
    assert auth_admin.login("admin", "admin123")
    caja_admin = CajaService(db, auth_admin)
    STATE["caja_id"] = caja_admin.abrir(STATE["admin_id"], 0.0)

    # El cajero retoma su sesion
    assert auth.login("cajero1", "clave123")

    # Consultar productos: SI puede
    prods = productos.listar_activos()
    assert len(prods) > 0
    prod = prods[0]

    # Abrir mesa y tomar pedido: SI puede
    mesas_disp = [m for m in mesas.listar() if m["estado"] == "DISPONIBLE"]
    mesa = mesas_disp[0]
    venta_id = ventas.abrir_venta(
        mesa["id"], auth.usuario_actual.id, STATE["caja_id"]
    )
    mesas.ocupar(mesa["id"], venta_id)
    ventas.agregar_detalle(
        venta_id, prod["id"], prod["nombre"], 2, prod["precio"]
    )

    # Leer SU venta: permitido
    fila = ventas.obtener_por_id(venta_id)
    assert fila and fila["usuario_id"] == auth.usuario_actual.id

    # Cobrar: SI puede (elige EFECTIVO o TRANSFERENCIA)
    assert ventas.cobrar(venta_id, "EFECTIVO") is True

    # Consultar historial: solo ve ventas propias
    propias = ventas.listar_con_filtros()
    assert len(propias) >= 1
    assert all(v["usuario_id"] == auth.usuario_actual.id for v in propias)
    STATE["venta_cajero_id"] = venta_id


def t06_cajero_no_ve_ventas_ajenas(db):
    """Restriccion real: una venta ajena -> PermissionError."""
    auth = STATE["auth"]
    auth.logout()
    assert auth.login("cajero2", "clave234")
    ventas = VentaService(db, auth)

    espera_permiso(lambda: ventas.obtener_por_id(STATE["venta_cajero_id"]))
    espera_permiso(lambda: ventas.obtener_detalles(STATE["venta_cajero_id"]))
    # El listado nunca le devuelve ventas de otros
    historial = ventas.listar_con_filtros()
    assert all(v["usuario_id"] == auth.usuario_actual.id for v in historial)

    # El ADMIN si ve todas
    auth.logout()
    assert auth.login("admin", "admin123")
    todas = VentaService(db, auth).listar_con_filtros()
    assert len(todas) >= 1
    STATE["auth"] = auth


def t07_venta_cerrada_solo_admin_la_anula(db):
    auth = STATE["auth"]
    # Un cajero NO puede anular ventas cerradas (comprobante historico)
    auth.logout()
    assert auth.login("cajero1", "clave123")
    ventas_cajero = VentaService(db, auth)
    espera_permiso(lambda: ventas_cajero.anular(STATE["venta_cajero_id"]))
    # El ADMIN si puede anular la venta cerrada
    auth.logout()
    assert auth.login("admin", "admin123")
    ventas = VentaService(db, auth)
    assert ventas.anular(STATE["venta_cajero_id"]) is True
    fila = db.fetchone(
        "SELECT estado FROM ventas WHERE id=?;", (STATE["venta_cajero_id"],)
    )
    assert fila["estado"] == "ANULADA"

def t08_administracion_de_usuarios_y_ultimo_admin(db):
    auth = STATE["auth"]
    auth.logout()
    assert auth.login("admin", "admin123")
    svc = UsuarioService(db, auth)

    # Listar: solo ADMIN
    usuarios = svc.listar()
    assert {"admin", "admin2", "cajero1", "cajero2"} <= {
        u["usuario"] for u in usuarios
    }

    # Editar un usuario (ADMIN)
    svc.actualizar(STATE["cajero2_id"], "Cajero Dos Editado", "cajero2", "CAJERO")

    # Desactivar/degradar ADMIN permitidos mientras queden otros activos,
    # pero SIEMPRE bloqueados cuando quedaria cero ADMIN activos.
    activos = [u for u in svc.listar()
               if u["rol"] == "ADMIN" and u["activo"] == 1]
    assert len(activos) >= 1
    ultimo = activos[-1]
    for u in activos[:-1]:
        svc.cambiar_estado(u["id"], False)   # legal: quedan otros ADMIN
    try:
        svc.cambiar_estado(ultimo["id"], False)
        raise AssertionError(
            f"Debio bloquear desactivar al ultimo ADMIN: {ultimo['usuario']}"
        )
    except ValueError:
        pass
    try:
        svc.actualizar(ultimo["id"], ultimo["nombre"],
                       ultimo["usuario"], "CAJERO")
        raise AssertionError("Debio bloquear degradar al ultimo ADMIN")
    except ValueError:
        pass
    # Restaurar estado para las siguientes pruebas
    for u in activos[:-1]:
        svc.cambiar_estado(u["id"], True)

    # ADMIN cambia la contrasena de otro usuario
    svc.cambiar_password(STATE["cajero1_id"], "clavenueva1")
    # El cajero cambia SU propia contrasena (no es admin)
    auth.logout()
    assert auth.login("cajero1", "clavenueva1")
    svc_cajero = UsuarioService(db, auth)
    assert svc_cajero.cambiar_mi_password("clavenueva1", "clavefinal1")
    assert auth.login("cajero1", "clavefinal1")
    # Pero NO puede cambiar la de otro usuario
    espera_permiso(
        lambda: svc_cajero.cambiar_password(STATE["admin_id"], "hackeada1")
    )
    # cambiar_mi_password exige la contrasena actual correcta
    try:
        svc_cajero.cambiar_mi_password("incorrecta", "otraclave1")
        raise AssertionError("Debio rechazar la contrasena actual incorrecta")
    except ValueError:
        pass


def t09_admin_hace_operaciones_criticas(db):
    """ADMIN: cerrar caja, backups, configuracion y reportes."""
    auth = STATE["auth"]
    auth.logout()
    assert auth.login("admin", "admin123")

    caja = CajaService(db, auth)
    resumen = caja.cerrar(STATE["caja_id"], 0.0, "cierre pruebas punto 3")
    assert resumen["diferencia"] == 0
    assert caja.historial(), "ADMIN consulta historial de cierres"

    backup = BackupService(db, auth)
    ruta = backup.crear_backup(destino=os.path.join(_TMP, "bk.db"))
    assert os.path.exists(ruta)

    config = ConfiguracionService(db, auth)
    config.set("nombre_negocio", "POS Pruebas")
    assert config.get("nombre_negocio") == "POS Pruebas"

    reportes = ReporteService(db, auth)
    resumen_ventas = reportes.resumen_ventas("2000-01-01", "2100-01-01")
    assert "total_vendido" in resumen_ventas
    STATE["auth"] = auth


def t10_operaciones_sin_sesion_quedan_denegadas(db):
    auth = AuthService(db)
    auth.logout()
    espera_permiso(lambda: ProductoService(db, auth).cambiar_precio(1, 1))
    espera_permiso(lambda: VentaService(db, auth).cobrar(1, "EFECTIVO"))
    espera_permiso(lambda: CajaService(db, auth).abrir(1, 0))


PRUEBAS = [
    t01_matriz_de_permisos,
    t02_login_y_sesion,
    t03_crear_usuarios_del_rol,
    t04_cajero_sin_permisos_de_administracion,
    t05_cajero_operaciones_de_su_rol,
    t06_cajero_no_ve_ventas_ajenas,
    t07_venta_cerrada_solo_admin_la_anula,
    t08_administracion_de_usuarios_y_ultimo_admin,
    t09_admin_hace_operaciones_criticas,
    t10_operaciones_sin_sesion_quedan_denegadas,
]


def main():
    db = DatabaseConnection()
    inicializar_base_de_datos(db)
    ejecutar_seeder(db)

    print("=" * 60)
    print(" PRUEBAS PUNTO 3 — LOGIN, USUARIOS Y PERMISOS")
    print("=" * 60)

    for fn in PRUEBAS:
        registrar(fn.__name__, fn, db)

    db.close()
    print("-" * 60)
    ok = sum(1 for _, exito, _ in RESULTADOS if exito)
    print(f" RESULTADO: {ok}/{len(RESULTADOS)} pruebas exitosas")
    fallos = [n for n, exito, _ in RESULTADOS if not exito]
    if fallos:
        print(" Fallaron:", ", ".join(fallos))
        sys.exit(1)
    print(" PUNTO 3 VALIDADO COMPLETAMENTE [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
