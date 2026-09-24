# -*- coding: utf-8 -*-
"""Smoke test de UI del PUNTO 5 - Cobro y caja (PySide6)."""
import os
import sys
import shutil
import tempfile

from PySide6.QtWidgets import QApplication

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_TMP = tempfile.mkdtemp(prefix="p5ui_")
import app.utils.paths as paths
paths.DB_PATH = os.path.join(_TMP, "pos.db")

from app.database.connection import DatabaseConnection
from app.database.migrations import inicializar_base_de_datos
from app.database.seeder import ejecutar_seeder
from app.services.auth_service import AuthService
from app.services.caja_service import CajaService
from app.ui.screens.mesas_screen import MesasScreen
from app.ui.screens.cobro_screen import DialogoCobro
from app.ui.screens.caja_screen import CajaScreen
from app.utils.helpers import formato_moneda

RESULTADOS = []
COMPROBANTES = []


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
    caja_id = cajas.abrir(auth.usuario_actual.id, 100000)

    pantalla = MesasScreen(db, auth)
    estado = {}

    def crear_pedido(indice=0):
        """Abre una mesa desde la UI, agrega un producto y devuelve los datos."""
        mesa = next(
            m for m in pantalla._ps.listar_mesas() if m["estado"] == "DISPONIBLE"
        )
        pantalla._seleccionar_mesa(mesa)
        pedido = pantalla._pedido
        producto = pedido._catalogo._servicio().catalogo_productos(True)[indice]
        pedido._catalogo._cambiar(producto["id"], +1)
        total = pantalla._ps.resumen_pedido(pedido._venta_id)["total"]
        return mesa, pedido._venta_id, total, producto["nombre"]

    def t01_dialogo_muestra_total_y_cambio():
        mesa, venta_id, total, _ = crear_pedido()
        estado["mesa1"] = mesa
        estado["venta1"] = venta_id
        estado["total1"] = total
        dialogo = DialogoCobro(db, auth, venta_id, mesa_nombre=mesa["nombre"])
        assert dialogo._total == total
        assert formato_moneda(total) in dialogo._lbl_total.text()
        dialogo._txt_recibido.setText(str(int(total + 12000)))
        esperado = formato_moneda(12000)
        assert esperado in dialogo._lbl_cambio.text(), (
            f"Cambio mostrado: {dialogo._lbl_cambio.text()}"
        )
        estado["dialogo1"] = dialogo

    def t02_cobro_efectivo_desde_dialogo():
        dialogo = estado["dialogo1"]
        datos = dialogo.cobrar()
        assert datos is not None, "El cobro devolvio None"
        assert datos["cambio"] == 12000
        assert datos["metodo_pago"] == "EFECTIVO"
        assert os.path.exists(datos["comprobante_ruta"])
        COMPROBANTES.append(datos["comprobante_ruta"])
        mesa = pantalla._ps.datos_mesa_activa(estado["mesa1"]["id"])
        assert mesa["estado"] == "DISPONIBLE"
        fila = db.fetchone(
            "SELECT estado, caja_id FROM ventas WHERE id=?;", (estado["venta1"],)
        )
        assert fila["estado"] == "CERRADA" and fila["caja_id"] == caja_id

    def t03_transferencia_desde_dialogo():
        _, venta_id, total, _ = crear_pedido(1)
        resumen_antes = cajas.actualizar_totales(caja_id)
        dialogo = DialogoCobro(db, auth, venta_id)
        dialogo._seleccionar_metodo("TRANSFERENCIA")
        assert dialogo.metodo() == "TRANSFERENCIA"
        assert not dialogo._panel_efectivo.isVisible()
        datos = dialogo.cobrar()
        assert datos is not None and datos["metodo_pago"] == "TRANSFERENCIA"
        assert datos["cambio"] is None
        COMPROBANTES.append(datos["comprobante_ruta"])
        resumen = cajas.actualizar_totales(caja_id)
        assert resumen["total_efectivo"] == resumen_antes["total_efectivo"]
        assert resumen["total_transferencia"] == round(
            resumen_antes["total_transferencia"] + total, 2
        )

    def t04_boton_cobrar_en_pedido():
        mesa = next(
            m for m in pantalla._ps.listar_mesas() if m["estado"] == "DISPONIBLE"
        )
        pantalla._seleccionar_mesa(mesa)
        pedido = pantalla._pedido
        assert pedido._btn_cobrar.isEnabled()
        pedido._catalogo._cambiar(
            pedido._catalogo._servicio().catalogo_productos(True)[0]["id"], +1
        )
        venta_id = pedido._venta_id
        dialogo = DialogoCobro(
            db, auth, venta_id, mesa_nombre=mesa["nombre"], parent=pedido
        )
        total = dialogo._total
        dialogo._txt_recibido.setText(str(int(total)))
        datos = dialogo.cobrar()
        assert datos["cambio"] == 0
        COMPROBANTES.append(datos["comprobante_ruta"])
        # La mesa vuelve a estar disponible en el tablero
        pantalla.refrescar()
        assert pantalla._ps.datos_mesa_activa(mesa["id"])["estado"] == "DISPONIBLE"

    def t05_pantalla_caja_muestra_totales():
        pantalla_caja = CajaScreen(db, auth)
        pantalla_caja.refrescar()
        assert "CAJA ABIERTA" in pantalla_caja._lbl_estado.text()
        resumen = cajas.actualizar_totales(caja_id)
        esperado = formato_moneda(resumen["efectivo_esperado"])
        assert esperado in pantalla_caja._detalles.text()
        assert resumen["total_efectivo"] > 0
        assert resumen["efectivo_esperado"] == round(
            resumen["monto_inicial"] + resumen["total_efectivo"], 2
        )

    registrar("t01_dialogo_muestra_total_y_cambio", t01_dialogo_muestra_total_y_cambio)
    registrar("t02_cobro_efectivo_desde_dialogo", t02_cobro_efectivo_desde_dialogo)
    registrar("t03_transferencia_desde_dialogo", t03_transferencia_desde_dialogo)
    registrar("t04_boton_cobrar_en_pedido", t04_boton_cobrar_en_pedido)
    registrar("t05_pantalla_caja_muestra_totales", t05_pantalla_caja_muestra_totales)

    db.close()
    for ruta in COMPROBANTES:
        try:
            os.remove(ruta)
        except OSError:
            pass
    print("-" * 60)
    ok = sum(1 for _, exito, _ in RESULTADOS if exito)
    print(f" RESULTADO: {ok}/{len(RESULTADOS)} smoke tests exitosos")
    fallos = [n for n, exito, _ in RESULTADOS if not exito]
    if fallos:
        print(" Fallaron:", ", ".join(fallos))
        sys.exit(1)
    print(" SMOKE UI PUNTO 5 [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()

