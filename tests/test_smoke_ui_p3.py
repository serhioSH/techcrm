
import sys
import os
import tempfile
import shutil
from PySide6.QtWidgets import QApplication

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_TMP = tempfile.mkdtemp(prefix="pos_smoke_")
import app.utils.paths as paths
paths.DB_PATH = os.path.join(_TMP, "pos_test.db")

from app.database.connection import DatabaseConnection
from app.database.migrations import inicializar_base_de_datos
from app.database.seeder import ejecutar_seeder
from app.services.auth_service import AuthService
from app.ui.login_window import LoginWindow
from app.ui.main_window import MainWindow
from app.ui.screens.usuarios_screen import UsuariosScreen
from app.ui.screens.productos_screen import ProductosScreen
from app.ui.widgets.dialogo_password import DialogoPassword

RESULTADOS = []
APP = None


def registrar(nombre, fn):
    try:
        fn()
        RESULTADOS.append((nombre, True, ""))
        print(f"  [ OK ] {nombre}")
    except Exception as e:
        RESULTADOS.append((nombre, False, f"{type(e).__name__}: {e}"))
        print(f"  [FALLA] {nombre} -> {e}")


def main():
    global APP
    APP = QApplication(sys.argv)
    APP.setStyle("Fusion")
    APP.setOrganizationName("POS_Tests")
    db = DatabaseConnection()
    inicializar_base_de_datos(db)
    ejecutar_seeder(db)

    print("=" * 60)
    print(" SMOKE TEST UI — PUNTO 3 (interfaz por rol + usuarios)")
    print("=" * 60)

    auth = AuthService(db)

    # Usuarios de prueba que necesitan los demas casos
    from app.services.usuario_service import UsuarioService
    auth.logout()
    assert auth.login("admin", "admin123")
    _svc_usuarios = UsuarioService(db, auth)
    for _nombre, _usuario, _clave in (
        ("Cajero Uno", "cajero1", "clavefinal1"),
        ("Cajero Dos", "cajero2", "clavefinal1"),
    ):
        if not db.fetchone(
            "SELECT id FROM usuarios WHERE usuario=?;", (_usuario,)
        ):
            _svc_usuarios.crear(_nombre, _usuario, _clave, "CAJERO")

    def t01_login_admin_abre_main():
        auth.logout()
        user = auth.login("admin", "admin123")
        assert user is not None and user.rol == "ADMIN"
        main = MainWindow(db, auth)
        assert main._usuario == user
        assert "usuarios" in main._pantallas
        assert "caja" in main._pantallas
        assert "configuracion" in main._pantallas
        assert "productos" in main._pantallas
        assert "reportes" in main._pantallas
        assert "historial" in main._pantallas
        usuarios_screen = main._pantallas["usuarios"]
        assert isinstance(usuarios_screen, UsuariosScreen)
        assert usuarios_screen.TITULO == "Usuarios"

    def t02_login_cajero_solo_navegacion_permitida():
        auth.logout()
        assert auth.login("cajero1", "clavefinal1") is not None
        main = MainWindow(db, auth)
        items_menu = {key for key, *_ in main._items_navegacion()}
        pantallas = set(main._pantallas.keys())
        assert pantallas == items_menu
        assert "usuarios" not in items_menu
        assert "productos" not in items_menu
        assert "configuracion" not in items_menu
        assert "mesas" in items_menu and "caja" in items_menu and "historial" in items_menu
        main._navegar("usuarios")
        assert main._stack.currentIndex() >= 0

    def t03_usuario_screen_carga_plantilla_del_admin():
        auth.logout()
        assert auth.login("admin", "admin123")
        pantalla = UsuariosScreen(db, auth)
        assert pantalla.TITULO == "Usuarios"
        assert pantalla._btn_nuevo is not None
        pantalla.refrescar()
        assert pantalla._tabla.rowCount() >= 3

    def t04_dialogo_password_admin_puede_editar_cajero():
        auth.logout()
        assert auth.login("admin", "admin123")
        cajero2_id = auth.login("cajero2", "clavefinal1").id
        auth.logout()
        assert auth.login("admin", "admin123")
        dialogo = DialogoPassword(db, auth, id_usuario=cajero2_id)
        assert dialogo._txt_nueva is not None

    def t05_cambiar_password_propio_via_dialogo():
        auth.logout()
        assert auth.login("cajero2", "clavefinal1")
        dialogo = DialogoPassword(db, auth, id_usuario=None)
        dialogo._txt_actual.setText("clavefinal1")
        dialogo._txt_nueva.setText("nuevoclavec2")
        dialogo._txt_confirma.setText("nuevoclavec2")
        dialogo._guardar()
        assert auth.login("cajero2", "nuevoclavec2")
        assert auth.login("cajero2", "clavefinal1") is None

    for fn in (
        t01_login_admin_abre_main,
        t02_login_cajero_solo_navegacion_permitida,
        t03_usuario_screen_carga_plantilla_del_admin,
        t04_dialogo_password_admin_puede_editar_cajero,
        t05_cambiar_password_propio_via_dialogo,
    ):
        registrar(fn.__name__, fn)

    db.close()
    print("-" * 60)
    ok = sum(1 for _, exito, _ in RESULTADOS if exito)
    fallos = [n for n, exito, _ in RESULTADOS if not exito]
    print(f" RESULTADO: {ok}/{len(RESULTADOS)} smoke tests exitosos")
    if fallos:
        print(" Fallaron:", ", ".join(fallos))
    else:
        print(" SMOKE UI PUNTO 3 [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
