# -*- coding: utf-8 -*-
"""Pruebas del PUNTO 9 - Apertura y cierre de caja (sin PySide6)."""
import os
import sys
import shutil
import sqlite3
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_TMP = tempfile.mkdtemp(prefix="p9test_")
import app.utils.paths as paths
paths.DB_PATH = os.path.join(_TMP, "pos.db")

from app.database.connection import DatabaseConnection
from app.database.migrations import inicializar_base_de_datos
from app.database.seeder import ejecutar_seeder
from app.services.auth_service import AuthService
from app.services.usuario_service import UsuarioService
from app.services.pedido_service import PedidoService
from app.services.caja_service import CajaService
from app.services.cobro_service import CobroService

RESULTADOS = []


def registrar(nombre, fn):
    try:
        fn()
        RESULTADOS.append((nombre, True, ""))
        print(f"  [ OK ] {nombre}")
    except Exception as e:
        RESULTADOS.append((nombre, False, f"{type(e).__name__}: {e}"))
        print(f"  [FALLA] {nombre} -> {e}")


def espera_error(fn, fragmento=""):
    try:
        fn()
    except (ValueError, PermissionError) as e:
        if fragmento and fragmento.lower() not in str(e).lower():
            raise AssertionError(f"Mensaje inesperado: {e}")
        return
    raise AssertionError("La operacion debio ser rechazada")

def main():
    db = DatabaseConnection()
    inicializar_base_de_datos(db)
    ejecutar_seeder(db)

    auth = AuthService(db)
    assert auth.login("admin", "admin123") is not None
    cajas = CajaService(db, auth)
    ps = PedidoService(db, auth)
    cobro = CobroService(db, auth)
    estado = {}

    def crear_pedido(indice_producto=0, cantidad=1):
        mesa = next(m for m in ps.listar_mesas() if m["estado"] == "DISPONIBLE")
        venta_id = ps.abrir_mesa(mesa["id"])
        producto = ps.catalogo_productos(True)[indice_producto]
        ps.agregar_producto(venta_id, producto["id"], cantidad)
        total = db.fetchone("SELECT total FROM ventas WHERE id=?;",
                            (venta_id,))["total"]
        return venta_id, total

    def t01_apertura_guarda_efectivo_inicial():
        caja_id = cajas.abrir(auth.usuario_actual.id, 200000)
        caja = cajas.caja_abierta()
        assert caja["id"] == caja_id
        assert caja["monto_inicial"] == 200000
        assert caja["fecha_apertura"], "Debe registrar la fecha de apertura"
        assert caja["usuario_nombre"] == "Administrador"
        assert caja["estado"] == "ABIERTA"
        estado["caja_id"] = caja_id

    def t02_no_se_puede_abrir_dos_veces():
        try:
            cajas.abrir(auth.usuario_actual.id, 1000)
            raise AssertionError("Debio rechazar la segunda apertura")
        except Exception as e:
            assert "UNIQUE" in str(e), f"Error inesperado: {e}"

    def t03_efectivo_esperado_y_transferencias_aparte():
        venta_id, total = crear_pedido(0, 1)          # 2500
        cobro.cobrar_efectivo(venta_id, total)
        venta_id, total = crear_pedido(1, 1)          # 8000
        cobro.cobrar_transferencia(venta_id)
        resumen = cajas.actualizar_totales(estado["caja_id"])
        assert resumen["monto_inicial"] == 200000
        assert resumen["total_efectivo"] == 2500
        assert resumen["total_transferencia"] == 8000
        assert resumen["total_general"] == 10500
        # Efectivo esperado = inicial + SOLO ventas en efectivo
        assert resumen["efectivo_esperado"] == 202500
        estado["resumen"] = resumen

    def t04_cierre_con_diferencia_faltante():
        contado = 200000 + 2500 - 10000      # faltan 10.000
        resultado = cajas.cerrar(estado["caja_id"], contado, "faltante de prueba")
        assert resultado["efectivo_esperado"] == 202500
        assert resultado["diferencia"] == 10000, (
            f"diferencia = esperado - contado: {resultado['diferencia']}"
        )
        cierre = db.fetchone(
            "SELECT estado, fecha_cierre, efectivo_esperado, efectivo_contado, "
            "diferencia, observaciones FROM cajas WHERE id=?;",
            (estado["caja_id"],),
        )
        assert cierre["estado"] == "CERRADA" and cierre["fecha_cierre"]
        assert cierre["efectivo_contado"] == contado
        assert cierre["diferencia"] == 10000
        assert cierre["observaciones"] == "faltante de prueba"

    def t05_diferencia_cuadra_y_sobrante():
        # Jornada 2: cuadra (diferencia 0)
        caja2 = cajas.abrir(auth.usuario_actual.id, 100000)
        venta_id, total = crear_pedido(2, 1)          # 5000
        cobro.cobrar_efectivo(venta_id, total)
        r2 = cajas.actualizar_totales(caja2)
        res2 = cajas.cerrar(caja2, r2["efectivo_esperado"], "cuadra")
        assert res2["diferencia"] == 0
        # Jornada 3: sobrante (diferencia negativa)
        caja3 = cajas.abrir(auth.usuario_actual.id, 0)
        res3 = cajas.cerrar(caja3, 500, "sobrante")
        assert res3["diferencia"] == -500

    def t06_historicos_de_cierres_solo_admin():
        # El cajero no puede consultar los historicos
        usuarios = UsuarioService(db, auth)
        if not db.fetchone("SELECT id FROM usuarios WHERE usuario='cajerop9';"):
            usuarios.crear("Cajero Nueve", "cajerop9", "clave123", "CAJERO")
        auth_cajero = AuthService(db)
        assert auth_cajero.login("cajerop9", "clave123") is not None
        cajas_cajero = CajaService(db, auth_cajero)
        espera_error(lambda: cajas_cajero.historial(), "permiso")
        # El ADMIN si: 3 jornadas, cada una con sus datos
        cierres = cajas.historial()
        assert len(cierres) == 3
        primera = [c for c in cierres if c["id"] == estado["caja_id"]][0]
        assert primera["usuario_nombre"] == "Administrador"
        assert primera["monto_inicial"] == 200000
        assert primera["total_efectivo"] == 2500
        assert primera["total_transferencia"] == 8000
        assert primera["total_general"] == 10500
        assert primera["efectivo_esperado"] == 202500
        assert primera["diferencia"] == 10000
        assert primera["fecha_cierre"], "Debe tener fecha de cierre"
        # Las transferencias quedan aparte (no suman al efectivo esperado)
        assert primera["efectivo_esperado"] == (
            primera["monto_inicial"] + primera["total_efectivo"]
        )

    def t07_cajero_no_abre_ni_cierra():
        auth_cajero = AuthService(db)
        assert auth_cajero.login("cajerop9", "clave123") is not None
        cajas_cajero = CajaService(db, auth_cajero)
        espera_error(lambda: cajas_cajero.abrir(auth_cajero.usuario_actual.id, 1000),
                     "permiso")
        caja = cajas.caja_abierta()
        if caja:
            espera_error(lambda: cajas_cajero.cerrar(caja["id"], 0), "permiso")

    def t08_nueva_jornada_no_mezcla_ventas():
        caja_nueva = cajas.abrir(auth.usuario_actual.id, 50000)
        venta_id, total = crear_pedido(0, 1)          # 2500
        cobro.cobrar_efectivo(venta_id, total)
        resumen = cajas.actualizar_totales(caja_nueva)
        # Solo cuenta las ventas de ESTA jornada
        assert resumen["total_efectivo"] == 2500
        assert resumen["efectivo_esperado"] == 52500
        estado["caja_nueva"] = caja_nueva

    def t09_sin_caja_no_se_puede_cobrar():
        cajas.cerrar(estado["caja_nueva"], 52500, "fin pruebas")
        venta_id, total = crear_pedido(0, 1)
        espera_error(lambda: cobro.cobrar_efectivo(venta_id, total), "caja")
        ps.cancelar_pedido(
            [m for m in ps.listar_mesas() if m["venta_activa_id"] == venta_id][0]["id"]
        )

    def t10_historico_persiste_tras_reinicio():
        """Los cierres quedan en el archivo y sobreviven a un reinicio."""
        conexion = sqlite3.connect(paths.DB_PATH)
        try:
            cerradas = conexion.execute(
                "SELECT COUNT(*) FROM cajas WHERE estado='CERRADA';"
            ).fetchone()[0]
            con_diferencia = conexion.execute(
                "SELECT diferencia FROM cajas WHERE id=?;",
                (estado["caja_id"],),
            ).fetchone()[0]
        finally:
            conexion.close()
        assert cerradas == 4
        assert con_diferencia == 10000

    registrar("t01_apertura_guarda_efectivo_inicial", t01_apertura_guarda_efectivo_inicial)
    registrar("t02_no_se_puede_abrir_dos_veces", t02_no_se_puede_abrir_dos_veces)
    registrar("t03_efectivo_esperado_y_transferencias_aparte", t03_efectivo_esperado_y_transferencias_aparte)
    registrar("t04_cierre_con_diferencia_faltante", t04_cierre_con_diferencia_faltante)
    registrar("t05_diferencia_cuadra_y_sobrante", t05_diferencia_cuadra_y_sobrante)
    registrar("t06_historicos_de_cierres_solo_admin", t06_historicos_de_cierres_solo_admin)
    registrar("t07_cajero_no_abre_ni_cierra", t07_cajero_no_abre_ni_cierra)
    registrar("t08_nueva_jornada_no_mezcla_ventas", t08_nueva_jornada_no_mezcla_ventas)
    registrar("t09_sin_caja_no_se_puede_cobrar", t09_sin_caja_no_se_puede_cobrar)
    registrar("t10_historico_persiste_tras_reinicio", t10_historico_persiste_tras_reinicio)

    db.close()
    print("-" * 60)
    ok = sum(1 for _, exito, _ in RESULTADOS if exito)
    print(f" RESULTADO: {ok}/{len(RESULTADOS)} pruebas exitosas")
    fallos = [n for n, exito, _ in RESULTADOS if not exito]
    if fallos:
        print(" Fallaron:", ", ".join(fallos))
        sys.exit(1)
    print(" PUNTO 9 VALIDADO COMPLETAMENTE [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()


