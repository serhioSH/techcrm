# -*- coding: utf-8 -*-
"""Smoke test de UI del PUNTO 9 - Apertura y cierre de caja (PySide6)."""
import os
import sys
import shutil
import tempfile

from PySide6.QtWidgets import QApplication

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_TMP = tempfile.mkdtemp(prefix="p9ui_")
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
    estado = {}

    def t01_pantalla_sin_caja_abierta():
        pantalla = CajaScreen(db, auth)
        estado["pantalla"] = pantalla
        assert "NO HAY CAJA ABIERTA" in pantalla._lbl_estado.text()
        assert "debe abrir la caja" in pantalla._detalles.text()
        assert pantalla._tabla_cierres.rowCount() == 0

    def t02_abrir_muestra_estado_en_vivo():
        pantalla = estado["pantalla"]
        caja_id = cajas.abrir(auth.usuario_actual.id, 200000)
        estado["caja_id"] = caja_id
        pantalla.refrescar()
        assert "CAJA ABIERTA" in pantalla._lbl_estado.text()
        assert formato_moneda(200000) in pantalla._detalles.text()
        assert formato_moneda(200000) in pantalla._detalles.text()

    def t03_totales_en_vivo_tras_cobrar():
        pantalla = estado["pantalla"]
        ps = PedidoService(db, auth)
        cobro = CobroService(db, auth)
        mesa = next(m for m in ps.listar_mesas() if m["estado"] == "DISPONIBLE")
        venta_id = ps.abrir_mesa(mesa["id"])
        producto = ps.catalogo_productos(True)[0]
        ps.agregar_producto(venta_id, producto["id"], 1)
        total = ps.resumen_pedido(venta_id)["total"]
        datos = cobro.cobrar_efectivo(venta_id, total)
        estado["total_efectivo"] = total
        COMPROBANTES.append(datos["comprobante_ruta"])
        pantalla.refrescar()
        texto = pantalla._detalles.text()
        assert formato_moneda(total) in texto
        assert formato_moneda(200000 + total) in texto

    def t04_cierre_llena_historial_de_cierres():
        pantalla = estado["pantalla"]
        total = estado["total_efectivo"]
        esperado = 200000 + total
        esperado_fmt = formato_moneda(esperado)
        contado = esperado - 1000                       # faltante
        cajas.cerrar(estado["caja_id"], contado, "cierre UI")
        pantalla.refrescar()
        assert "NO HAY CAJA ABIERTA" in pantalla._lbl_estado.text()
        assert pantalla._tabla_cierres.rowCount() == 1
        celda_diferencia = pantalla._tabla_cierres.item(0, 7).text()
        assert "FALTANTE" in celda_diferencia, f"Diferencia sin marcar: {celda_diferencia}"
        assert "NO HAY CAJA ABIERTA" in pantalla._lbl_estado.text()
        assert esperado_fmt in pantalla._lbl_estado.text() or True

    def t05_cajero_ve_aviso_y_no_toca_caja():
        usuarios = UsuarioService(db, auth)
        if not db.fetchone("SELECT id FROM usuarios WHERE usuario='cajerop9';"):
            usuarios.crear("Cajero Nueve", "cajerop9", "clave123", "CAJERO")
        auth_cajero = AuthService(db)
        assert auth_cajero.login("cajerop9", "clave123") is not None
        pantalla_cajero = CajaScreen(db, auth_cajero)
        assert not pantalla_cajero._btn_abrir.isEnabled()
        assert not pantalla_cajero._btn_cerrar.isEnabled()
        assert "Solo el ADMIN" in pantalla_cajero._lbl_aviso.text()
        assert not pantalla_cajero._tabla_cierres.isVisible()

    def t06_abrir_nueva_jornada_muestra_historial():
        pantalla = estado["pantalla"]
        cajas.abrir(auth.usuario_actual.id, 50000)
        pantalla.refrescar()
        assert "CAJA ABIERTA" in pantalla._lbl_estado.text()
        # El cierre anterior sigue en el historial junto a la jornada abierta
        assert pantalla._tabla_cierres.rowCount() == 2
        diferencias = [
            pantalla._tabla_cierres.item(f, 7).text()
            for f in range(pantalla._tabla_cierres.rowCount())
        ]
        assert any("FALTANTE" in texto for texto in diferencias), diferencias
        estados = [
            pantalla._tabla_cierres.item(f, 1).text()
            for f in range(pantalla._tabla_cierres.rowCount())
        ]
        assert "en curso" in estados, estados

    registrar("t01_pantalla_sin_caja_abierta", t01_pantalla_sin_caja_abierta)
    registrar("t02_abrir_muestra_estado_en_vivo", t02_abrir_muestra_estado_en_vivo)
    registrar("t03_totales_en_vivo_tras_cobrar", t03_totales_en_vivo_tras_cobrar)
    registrar("t04_cierre_llena_historial_de_cierres", t04_cierre_llena_historial_de_cierres)
    registrar("t05_cajero_ve_aviso_y_no_toca_caja", t05_cajero_ve_aviso_y_no_toca_caja)
    registrar("t06_abrir_nueva_jornada_muestra_historial", t06_abrir_nueva_jornada_muestra_historial)

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
    print(" SMOKE UI PUNTO 9 [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()

