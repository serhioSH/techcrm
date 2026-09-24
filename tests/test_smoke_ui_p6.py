# -*- coding: utf-8 -*-
"""Smoke test de UI del PUNTO 6 - Configuracion e impresion (PySide6)."""
import os
import sys
import shutil
import tempfile

from PySide6.QtWidgets import QApplication

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_TMP = tempfile.mkdtemp(prefix="p6ui_")
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
from app.services.configuracion_service import ConfiguracionService
from app.services.comprobante_service import ComprobanteService
from app.printing.printer_manager import PrinterManager
from app.ui.screens.configuracion_screen import ConfiguracionScreen

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
    config = ConfiguracionService(db, auth)
    estado = {}

    def t01_pantalla_carga_valores_guardados():
        config.set_varios({
            "nombre_negocio": "Comidas La 10",
            "direccion": "Av Siempre Viva 742",
            "telefono": "3001112233",
            "mensaje_final": "Gracias por su compra",
            "ancho_ticket_mm": "80",
        })
        pantalla = ConfiguracionScreen(db, auth)
        assert pantalla._txt_nombre.text() == "Comidas La 10"
        assert pantalla._txt_direccion.text() == "Av Siempre Viva 742"
        assert pantalla._txt_telefono.text() == "3001112233"
        assert pantalla._txt_mensaje.text() == "Gracias por su compra"
        assert pantalla._cmb_ancho.currentText() == "80"
        estado["pantalla"] = pantalla

    def t02_editar_y_guardar_persiste():
        pantalla = estado["pantalla"]
        pantalla._txt_nombre.setText("Comidas El Punto")
        pantalla._txt_direccion.setText("Calle 10 # 5-25")
        pantalla._txt_telefono.setText("3216549870")
        pantalla._txt_mensaje.setText("¡Vuelva pronto!")
        pantalla._cmb_impresora.setCurrentText("POS-80 Termica")
        pantalla._cmb_ancho.setCurrentText("58")
        ok, mensaje = pantalla.guardar()
        assert ok, mensaje
        assert config.get("nombre_negocio") == "Comidas El Punto"
        assert config.get("impresora") == "POS-80 Termica"
        assert config.get("ancho_ticket_mm") == "58"

    def t03_combo_impresoras_del_sistema():
        pantalla = estado["pantalla"]
        pantalla.refrescar()
        # El combo es editable: siempre se puede escribir el nombre
        assert pantalla._cmb_impresora.isEditable()
        lista = PrinterManager.listar_impresoras()
        assert isinstance(lista, list)

    def t04_probar_impresion_falla_suave():
        pantalla = estado["pantalla"]
        pantalla._cmb_impresora.setCurrentText("IMPRESORA_INEXISTENTE_XYZ")
        ok, mensaje = pantalla.probar_impresion()
        assert ok is False and mensaje

    def t05_cajero_no_puede_guardar():
        usuarios = UsuarioService(db, auth)
        if not db.fetchone("SELECT id FROM usuarios WHERE usuario='cajerop6';"):
            usuarios.crear("Cajero P6", "cajerop6", "clave123", "CAJERO")
        auth_cajero = AuthService(db)
        assert auth_cajero.login("cajerop6", "clave123") is not None
        pantalla_cajero = ConfiguracionScreen(db, auth_cajero)
        pantalla_cajero._txt_nombre.setText("Hackeo")
        ok, mensaje = pantalla_cajero.guardar()
        assert ok is False and "permiso" in mensaje.lower()
        assert config.get("nombre_negocio") == "Comidas El Punto"

    def t06_ticket_con_ancho_configurado():
        """Con ancho 58 guardado, el comprobante respeta 32 columnas."""
        # Caja abierta + venta cobrada
        cajas = CajaService(db, auth)
        caja_id = cajas.abrir(auth.usuario_actual.id, 0)
        ps = PedidoService(db, auth)
        cobro = CobroService(db, auth)
        mesa = next(m for m in ps.listar_mesas() if m["estado"] == "DISPONIBLE")
        venta_id = ps.abrir_mesa(mesa["id"])
        producto = ps.catalogo_productos(True)[0]
        ps.agregar_producto(venta_id, producto["id"], 1)
        total = ps.resumen_pedido(venta_id)["total"]
        datos = cobro.cobrar_efectivo(venta_id, total)
        COMPROBANTES.append(datos["comprobante_ruta"])
        texto = ComprobanteService(db).generar_texto(venta_id)
        lineas = texto.splitlines()
        maximo = max(len(linea) for linea in lineas)
        assert maximo <= 32, f"Linea de {maximo} excede 32 (ancho 58 configurado)"
        # Volver el ancho a 80 para dejar configuracion razonable
        config.set("ancho_ticket_mm", "80")

    registrar("t01_pantalla_carga_valores_guardados", t01_pantalla_carga_valores_guardados)
    registrar("t02_editar_y_guardar_persiste", t02_editar_y_guardar_persiste)
    registrar("t03_combo_impresoras_del_sistema", t03_combo_impresoras_del_sistema)
    registrar("t04_probar_impresion_falla_suave", t04_probar_impresion_falla_suave)
    registrar("t05_cajero_no_puede_guardar", t05_cajero_no_puede_guardar)
    registrar("t06_ticket_con_ancho_configurado", t06_ticket_con_ancho_configurado)

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
    print(" SMOKE UI PUNTO 6 [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()

