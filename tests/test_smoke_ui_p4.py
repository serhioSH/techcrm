# -*- coding: utf-8 -*-
"""Smoke test de UI del PUNTO 4 - Mesas y pedidos (PySide6)."""
import os
import sys
import shutil
import tempfile

from PySide6.QtWidgets import QApplication

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_TMP = tempfile.mkdtemp(prefix="p4ui_")
import app.utils.paths as paths
paths.DB_PATH = os.path.join(_TMP, "pos.db")

from app.database.connection import DatabaseConnection
from app.database.migrations import inicializar_base_de_datos
from app.database.seeder import ejecutar_seeder
from app.services.auth_service import AuthService
from app.ui.screens.mesas_screen import MesasScreen
from app.ui.screens.pedido_screen import PedidoScreen

RESULTADOS = []


def registrar(nombre, fn):
    try:
        fn()
        RESULTADOS.append((nombre, True, ""))
        print(f"  [ OK ] {nombre}")
    except Exception as e:
        RESULTADOS.append((nombre, False, f"{type(e).__name__}: {e}"))
        print(f"  [FALLA] {nombre} -> {e}")


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    db = DatabaseConnection()
    inicializar_base_de_datos(db)
    ejecutar_seeder(db)
    auth = AuthService(db)
    assert auth.login("admin", "admin123") is not None

    pantalla = MesasScreen(db, auth)
    estado = {}

    def t01_tablero_visual():
        pantalla.refrescar()
        assert pantalla._stack.currentWidget() is pantalla._pagina_mesas
        assert pantalla._grid.count() == 12, (
            f"Se esperaban 12 mesas y hay {pantalla._grid.count()}"
        )

    def t02_abrir_mesa_muestra_pedido():
        mesa = next(
            m for m in pantalla._ps.listar_mesas() if m["estado"] == "DISPONIBLE"
        )
        estado["mesa_id"] = mesa["id"]
        pantalla._seleccionar_mesa(mesa)
        assert isinstance(pantalla._pedido, PedidoScreen)
        assert pantalla._stack.currentWidget() is pantalla._pedido
        m = pantalla._ps.datos_mesa_activa(mesa["id"])
        assert m["estado"] == "OCUPADA" and m["venta_activa_id"] is not None
        estado["venta_id"] = m["venta_activa_id"]

    def t03_catalogo_agrega_y_calcula_total():
        pedido = pantalla._pedido
        producto = pedido._catalogo._servicio().catalogo_productos(True)[0]
        pedido._catalogo._cambiar(producto["id"], +1)
        pedido._catalogo._cambiar(producto["id"], +1)
        assert pedido._tabla.rowCount() == 1
        assert pedido._tabla.item(0, 1).text() == "2"
        resumen = pantalla._ps.resumen_pedido(estado["venta_id"])
        assert resumen["total"] == producto["precio"] * 2

    def t04_bajar_cantidad_y_quitar():
        pedido = pantalla._pedido
        producto = pedido._catalogo._servicio().catalogo_productos(True)[0]
        pedido._catalogo._cambiar(producto["id"], -1)
        assert pedido._tabla.item(0, 1).text() == "1"
        pedido._catalogo._cambiar(producto["id"], -1)
        assert pedido._tabla.rowCount() == 0
        assert pantalla._ps.resumen_pedido(estado["venta_id"])["total"] == 0

    def t05_cancelar_libera_mesa():
        pedido = pantalla._pedido
        producto = pedido._catalogo._servicio().catalogo_productos(True)[0]
        pedido._catalogo._cambiar(producto["id"], +1)
        pedido.cancelar_pedido()
        m = pantalla._ps.datos_mesa_activa(estado["mesa_id"])
        assert m["estado"] == "DISPONIBLE" and m["venta_activa_id"] is None
        assert pantalla._stack.currentWidget() is pantalla._pagina_mesas

    def t06_pedido_abierto_persiste():
        """Un pedido abierto sobrevive al 'reinicio' (nueva pantalla + SQLite)."""
        mesa = next(
            m for m in pantalla._ps.listar_mesas() if m["estado"] == "DISPONIBLE"
        )
        pantalla._seleccionar_mesa(mesa)
        pedido = pantalla._pedido
        producto = pedido._catalogo._servicio().catalogo_productos(True)[0]
        pedido._catalogo._cambiar(producto["id"], +1)
        venta_id = pantalla._ps.datos_mesa_activa(mesa["id"])["venta_activa_id"]

        otra_pantalla = MesasScreen(db, auth)
        resumen = otra_pantalla._ps.resumen_pedido(venta_id)
        assert resumen["total"] == producto["precio"]
        assert otra_pantalla._ps.datos_mesa_activa(mesa["id"])["estado"] == "OCUPADA"
        # limpieza: cancelar el pedido abierto
        otra_pantalla._seleccionar_mesa(
            otra_pantalla._ps.datos_mesa_activa(mesa["id"])
        )
        otra_pantalla._pedido.cancelar_pedido()

    registrar("t01_tablero_visual", t01_tablero_visual)
    registrar("t02_abrir_mesa_muestra_pedido", t02_abrir_mesa_muestra_pedido)
    registrar("t03_catalogo_agrega_y_calcula_total", t03_catalogo_agrega_y_calcula_total)
    registrar("t04_bajar_cantidad_y_quitar", t04_bajar_cantidad_y_quitar)
    registrar("t05_cancelar_libera_mesa", t05_cancelar_libera_mesa)
    registrar("t06_pedido_abierto_persiste", t06_pedido_abierto_persiste)

    db.close()
    print("-" * 60)
    ok = sum(1 for _, exito, _ in RESULTADOS if exito)
    print(f" RESULTADO: {ok}/{len(RESULTADOS)} smoke tests exitosos")
    fallos = [n for n, exito, _ in RESULTADOS if not exito]
    if fallos:
        print(" Fallaron:", ", ".join(fallos))
        sys.exit(1)
    print(" SMOKE UI PUNTO 4 [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()

