# -*- coding: utf-8 -*-
"""Smoke test de UI del PUNTO 7 - Historial de ventas (PySide6)."""
import os
import sys
import shutil
import tempfile

from PySide6.QtWidgets import QApplication

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_TMP = tempfile.mkdtemp(prefix="p7ui_")
import app.utils.paths as paths
paths.DB_PATH = os.path.join(_TMP, "pos.db")

from app.database.connection import DatabaseConnection
from app.database.migrations import inicializar_base_de_datos
from app.database.seeder import ejecutar_seeder
from app.services.auth_service import AuthService
from app.services.pedido_service import PedidoService
from app.services.caja_service import CajaService
from app.services.cobro_service import CobroService
from app.ui.screens.historial_screen import HistorialScreen, DialogoDetalleVenta

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

    cajas = CajaService(db, auth)
    cajas.abrir(auth.usuario_actual.id, 0)
    ps = PedidoService(db, auth)
    cobro = CobroService(db, auth)

    def crear_venta(nombre_mesa, indice_producto, metodo):
        mesa = next(
            m for m in ps.listar_mesas() if m["nombre"] == nombre_mesa
        )
        venta_id = ps.abrir_mesa(mesa["id"])
        producto = ps.catalogo_productos(True)[indice_producto]
        ps.agregar_producto(venta_id, producto["id"], 1)
        total = db.fetchone(
            "SELECT total FROM ventas WHERE id=?;", (venta_id,)
        )["total"]
        if metodo == "EFECTIVO":
            cobro.cobrar_efectivo(venta_id, total)
        else:
            cobro.cobrar_transferencia(venta_id)
        return venta_id

    venta1 = crear_venta("Mesa 1", 0, "EFECTIVO")
    venta2 = crear_venta("Mesa 2", 1, "TRANSFERENCIA")
    estado = {}

    pantalla = HistorialScreen(db, auth)

    def t01_pantalla_carga_y_tabla_llena():
        filas = pantalla.buscar()
        assert len(filas) == 2, f"Se esperaban 2 ventas: {len(filas)}"
        assert pantalla._tabla.rowCount() == 2
        assert "nunca se eliminan" in pantalla._lbl_info.text()

    def t02_filtro_por_metodo():
        pantalla._cmb_metodo.setCurrentText("EFECTIVO")
        filas = pantalla.buscar()
        assert len(filas) == 1
        assert filas[0]["metodo_pago"] == "EFECTIVO"
        assert filas[0]["id"] == venta1

    def t03_filtro_por_consecutivo():
        pantalla._cmb_metodo.setCurrentText("Todos")
        consecutivo = pantalla.buscar()[0]["consecutivo"]
        pantalla._spin_consecutivo.setValue(consecutivo)
        filas = pantalla.buscar()
        assert len(filas) == 1
        assert filas[0]["consecutivo"] == consecutivo

    def t04_dialogo_detalle_y_reimpresion():
        pantalla._spin_consecutivo.setValue(0)
        filas = pantalla.buscar()
        assert len(filas) == 2
        pantalla._tabla.selectRow(0)
        venta_id = pantalla._id_seleccionado()
        assert venta_id in (venta1, venta2)
        dialogo = DialogoDetalleVenta(db, auth, venta_id)
        assert dialogo._venta_id == venta_id
        assert dialogo._tabla.rowCount() >= 1
        assert "TOTAL" in dialogo._lbl_total.text()
        # Reimprimir sin impresora configurada: fallo suave, venta intacta
        ok, mensaje = dialogo.reimprimir()
        assert ok is False and mensaje
        fila = db.fetchone(
            "SELECT estado, metodo_pago FROM ventas WHERE id=?;", (venta_id,)
        )
        assert fila["estado"] == "CERRADA"
        assert fila["metodo_pago"] in ("EFECTIVO", "TRANSFERENCIA")

    def t05_limpiar_filtros_restaura_historial():
        pantalla._spin_consecutivo.setValue(999)
        assert pantalla.buscar() == []
        pantalla._limpiar()
        filas = pantalla.buscar()
        assert len(filas) == 2
        assert pantalla._cmb_metodo.currentText() == "Todos"

    registrar("t01_pantalla_carga_y_tabla_llena", t01_pantalla_carga_y_tabla_llena)
    registrar("t02_filtro_por_metodo", t02_filtro_por_metodo)
    registrar("t03_filtro_por_consecutivo", t03_filtro_por_consecutivo)
    registrar("t04_dialogo_detalle_y_reimpresion", t04_dialogo_detalle_y_reimpresion)
    registrar("t05_limpiar_filtros_restaura_historial", t05_limpiar_filtros_restaura_historial)

    db.close()
    print("-" * 60)
    ok = sum(1 for _, exito, _ in RESULTADOS if exito)
    print(f" RESULTADO: {ok}/{len(RESULTADOS)} smoke tests exitosos")
    fallos = [n for n, exito, _ in RESULTADOS if not exito]
    if fallos:
        print(" Fallaron:", ", ".join(fallos))
        sys.exit(1)
    print(" SMOKE UI PUNTO 7 [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()

