# -*- coding: utf-8 -*-
"""Pruebas del PUNTO 6 - Impresora termica y comprobante (sin PySide6)."""
import os
import sys
import shutil
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_TMP = tempfile.mkdtemp(prefix="p6test_")
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
from app.printing import escpos

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
    db = DatabaseConnection()
    inicializar_base_de_datos(db)
    ejecutar_seeder(db)

    auth = AuthService(db)
    assert auth.login("admin", "admin123") is not None
    config = ConfiguracionService(db, auth)
    ps = PedidoService(db, auth)
    cajas = CajaService(db, auth)
    cobro = CobroService(db, auth)
    comprobante = ComprobanteService(db)
    estado = {}

    # Datos del negocio configurables
    config.set_varios({
        "nombre_negocio": "Comidas El Punto",
        "direccion": "Calle 10 # 5-25",
        "telefono": "3216549870",
        "mensaje_final": "¡Vuelva pronto!",
        "ancho_ticket_mm": "80",
    })

    # Caja abierta + una venta cerrada para las pruebas de impresion
    caja_id = cajas.abrir(auth.usuario_actual.id, 50000)
    mesa = next(m for m in ps.listar_mesas() if m["estado"] == "DISPONIBLE")
    venta_id = ps.abrir_mesa(mesa["id"])
    producto = ps.catalogo_productos(True)[0]
    ps.agregar_producto(venta_id, producto["id"], 2)
    total = ps.resumen_pedido(venta_id)["total"]
    datos = cobro.cobrar_efectivo(venta_id, total + 1000)
    COMPROBANTES.append(datos["comprobante_ruta"])
    estado["venta_id"] = venta_id
    estado["total"] = total

    def t01_impresoras_sin_error():
        lista = PrinterManager.listar_impresoras()
        assert isinstance(lista, list)
        assert all(isinstance(x, str) for x in lista)
        assert isinstance(PrinterManager.impresora_defecto(), str)

    def t02_ticket_58mm_respete_ancho():
        config.set("ancho_ticket_mm", "58")
        texto = comprobante.generar_texto(estado["venta_id"])
        lineas = texto.splitlines()
        maximo = max(len(linea) for linea in lineas)
        assert maximo <= 32, f"Linea de {maximo} caracteres excede 32 (58mm)"
        assert len(lineas) <= 45, f"Ticket demasiado largo: {len(lineas)} lineas"

    def t03_ticket_80mm_respete_ancho():
        config.set("ancho_ticket_mm", "80")
        texto = comprobante.generar_texto(estado["venta_id"])
        lineas = texto.splitlines()
        maximo = max(len(linea) for linea in lineas)
        assert maximo <= 48, f"Linea de {maximo} caracteres excede 48 (80mm)"

    def t04_ticket_incluye_campos_obligatorios():
        texto = comprobante.generar_texto(estado["venta_id"])
        esperados = [
            "Comidas El Punto",       # nombre negocio
            "Calle 10 # 5-25",        # direccion
            "Tel: 3216549870",        # telefono
            "Comprobante: #1",        # consecutivo
            "Mesa:",                  # mesa
            "Administrador",          # cajero
            producto["nombre"],       # producto
            "EFECTIVO",               # metodo de pago
            "¡Vuelva pronto!",        # mensaje final
        ]
        for esperado in esperados:
            assert esperado in texto, f"Falta en el ticket: {esperado}"
        # fecha y hora de la venta
        venta = db.fetchone("SELECT fecha_hora FROM ventas WHERE id=?;",
                            (estado["venta_id"],))
        partes = venta["fecha_hora"].split(" ")
        assert f"Fecha: {partes[0]}" in texto
        assert f"Hora:  {partes[1][:5]}" in texto or f"Hora:  {partes[1]}" in texto
        # sin NIT en el comprobante (restaurante local)
        assert "NIT" not in texto
        # total correcto (formato: $ + numero alineado a 10)
        assert f"$ {estado['total']:>10.0f}" in texto

    def t05_reimpresion_tras_reinicio():
        """La venta cerrada se reimprime n veces leyendo desde SQLite."""
        texto_antes = comprobante.generar_texto(estado["venta_id"])

        import sqlite3

        class ConexionFresca:
            """Conexion nueva al mismo archivo (simula reinicio de la app)."""

            def __init__(self, ruta):
                self._ruta = ruta

            def _consultar(self, sql, params, unico):
                conexion = sqlite3.connect(self._ruta)
                conexion.row_factory = sqlite3.Row
                try:
                    cursor = conexion.execute(sql, params)
                    if unico:
                        fila = cursor.fetchone()
                        return dict(fila) if fila else None
                    return [dict(r) for r in cursor.fetchall()]
                finally:
                    conexion.close()

            def fetchone(self, sql, params=()):
                return self._consultar(sql, params, True)

            def fetchall(self, sql, params=()):
                return self._consultar(sql, params, False)

        servicio2 = ComprobanteService(ConexionFresca(paths.DB_PATH))
        textos = [servicio2.generar_texto(estado["venta_id"]) for _ in range(3)]
        for texto in textos:
            assert texto == texto_antes, "La reimpresion cambio el ticket"

    def t06_logo_escpos_raster():
        from PIL import Image
        ruta_logo = os.path.join(_TMP, "logo.png")
        Image.new("L", (8, 8), 0).save(ruta_logo)   # imagen 8x8 negra
        datos = escpos.logo_escpos(ruta_logo, ancho_max=576)
        assert datos.startswith(b"\x1d\x76\x30\x00"), "Cabecera GS v 0 ausente"
        assert b"\xff" in datos, "Los pixeles negros no se rasterizaron"
        assert escpos.logo_escpos("") == b""
        assert escpos.logo_escpos(os.path.join(_TMP, "no_existe.png")) == b""

    def t07_ticket_bytes_logo_y_corte():
        ruta_logo = os.path.join(_TMP, "logo.png")
        texto = comprobante.generar_texto(estado["venta_id"])
        crudo = escpos.construir_ticket(texto, ruta_logo, "80")
        assert crudo.startswith(b"\x1b@"), "Falta el reinicio ESC @"
        assert b"\x1d\x76\x30" in crudo, "Falta el logo raster"
        assert b"\x1d\x56\x41\x10" in crudo, "Falta el corte de papel"
        assert "Comidas El Punto".encode("cp850") in crudo
        crudo_sin_logo = escpos.construir_ticket(texto, None, "58")
        assert b"\x1d\x76\x30" not in crudo_sin_logo

    def t08_guardar_impresora_en_configuracion():
        config.set("impresora", "POS-80")
        assert config.get("impresora") == "POS-80"
        usuarios = UsuarioService(db, auth)
        if not db.fetchone("SELECT id FROM usuarios WHERE usuario='cajerop6';"):
            usuarios.crear("Cajero P6", "cajerop6", "clave123", "CAJERO")
        auth_cajero = AuthService(db)
        assert auth_cajero.login("cajerop6", "clave123") is not None
        config_cajero = ConfiguracionService(db, auth_cajero)
        try:
            config_cajero.set("impresora", "OTRA")
            raise AssertionError("El cajero no debe cambiar la configuracion")
        except PermissionError:
            pass
        assert config.get("impresora") == "POS-80"

    def t09_impresion_sin_impresora_configurada():
        config.set("impresora", "")
        ok, mensaje = cobro.imprimir_comprobante(estado["venta_id"])
        assert ok is False and "impresora" in mensaje.lower()

    def t10_impresion_a_impresora_inexistente_falla_suave():
        config.set("impresora", "IMPRESORA_INEXISTENTE_XYZ")
        ok, mensaje = cobro.imprimir_comprobante(estado["venta_id"])
        assert ok is False

    def t11_reimprimir_no_altera_venta_ni_caja():
        resumen_antes = cajas.actualizar_totales(caja_id)
        for _ in range(3):
            cobro.imprimir_comprobante(estado["venta_id"])
        fila = db.fetchone(
            "SELECT estado, metodo_pago FROM ventas WHERE id=?;",
            (estado["venta_id"],),
        )
        assert fila["estado"] == "CERRADA" and fila["metodo_pago"] == "EFECTIVO"
        resumen_despues = cajas.actualizar_totales(caja_id)
        assert resumen_despues["total_general"] == resumen_antes["total_general"]

    registrar("t01_impresoras_sin_error", t01_impresoras_sin_error)
    registrar("t02_ticket_58mm_respete_ancho", t02_ticket_58mm_respete_ancho)
    registrar("t03_ticket_80mm_respete_ancho", t03_ticket_80mm_respete_ancho)
    registrar("t04_ticket_incluye_campos_obligatorios", t04_ticket_incluye_campos_obligatorios)
    registrar("t05_reimpresion_tras_reinicio", t05_reimpresion_tras_reinicio)
    registrar("t06_logo_escpos_raster", t06_logo_escpos_raster)
    registrar("t07_ticket_bytes_logo_y_corte", t07_ticket_bytes_logo_y_corte)
    registrar("t08_guardar_impresora_en_configuracion", t08_guardar_impresora_en_configuracion)
    registrar("t09_impresion_sin_impresora_configurada", t09_impresion_sin_impresora_configurada)
    registrar("t10_impresion_a_impresora_inexistente_falla_suave", t10_impresion_a_impresora_inexistente_falla_suave)
    registrar("t11_reimprimir_no_altera_venta_ni_caja", t11_reimprimir_no_altera_venta_ni_caja)

    db.close()
    for ruta in COMPROBANTES:
        try:
            os.remove(ruta)
        except OSError:
            pass
    print("-" * 60)
    ok = sum(1 for _, exito, _ in RESULTADOS if exito)
    print(f" RESULTADO: {ok}/{len(RESULTADOS)} pruebas exitosas")
    fallos = [n for n, exito, _ in RESULTADOS if not exito]
    if fallos:
        print(" Fallaron:", ", ".join(fallos))
        sys.exit(1)
    print(" PUNTO 6 VALIDADO COMPLETAMENTE [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()

