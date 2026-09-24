# -*- coding: utf-8 -*-
"""Pruebas del PUNTO 5 - Cobro, caja y comprobante (sin PySide6)."""
import os
import sys
import glob
import shutil
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_TMP = tempfile.mkdtemp(prefix="p5test_")
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
ARCHIVOS_ANTES = set(glob.glob(os.path.join(paths.COMPROBANTES_PATH, "*.txt")))


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
    ps = PedidoService(db, auth)
    cajas = CajaService(db, auth)
    cobro = CobroService(db, auth)
    estado = {"admin_id": auth.usuario_actual.id}

    def crear_pedido(cantidad=2, indice_producto=0):
        mesa = next(m for m in ps.listar_mesas() if m["estado"] == "DISPONIBLE")
        venta_id = ps.abrir_mesa(mesa["id"])
        producto = ps.catalogo_productos(True)[indice_producto]
        ps.agregar_producto(venta_id, producto["id"], cantidad)
        total = ps.resumen_pedido(venta_id)["total"]
        return venta_id, total, mesa["id"], producto

    def t01_sin_caja_abierta_no_se_cobra():
        venta_id, total, mesa_id, _ = crear_pedido(1)
        espera_error(lambda: cobro.cobrar_efectivo(venta_id, total), "caja")
        ps.cancelar_pedido(mesa_id)

    def t02_abrir_caja():
        estado["caja_id"] = cajas.abrir(estado["admin_id"], 100000)
        assert cajas.caja_abierta()["id"] == estado["caja_id"]

    def t03_cobro_efectivo_calcula_cambio():
        venta_id, total, mesa_id, _ = crear_pedido(2)
        recibido = total + 5000
        datos = cobro.cobrar_efectivo(venta_id, recibido)
        assert datos["cambio"] == 5000, f"Cambio incorrecto: {datos['cambio']}"
        assert datos["total"] == total
        assert datos["metodo_pago"] == "EFECTIVO"
        fila = db.fetchone(
            "SELECT estado, metodo_pago, cobro_procesado, caja_id FROM ventas WHERE id=?;",
            (venta_id,),
        )
        assert fila["estado"] == "CERRADA"
        assert fila["metodo_pago"] == "EFECTIVO"
        assert fila["cobro_procesado"] == 1
        assert fila["caja_id"] == estado["caja_id"]
        estado["venta_efectivo"] = venta_id
        estado["total_efectivo"] = total

    def t04_transferencia_no_suma_al_efectivo():
        venta_id, total, _, _ = crear_pedido(1)
        resumen_antes = cajas.actualizar_totales(estado["caja_id"])
        datos = cobro.cobrar_transferencia(venta_id)
        assert datos["metodo_pago"] == "TRANSFERENCIA"
        assert datos["cambio"] is None
        resumen = cajas.actualizar_totales(estado["caja_id"])
        assert resumen["total_efectivo"] == resumen_antes["total_efectivo"], (
            "La transferencia NO debe aumentar el efectivo de caja"
        )
        assert resumen["total_transferencia"] == round(
            resumen_antes["total_transferencia"] + total, 2
        )
        assert resumen["efectivo_esperado"] == round(
            resumen["monto_inicial"] + resumen["total_efectivo"], 2
        )

    def t05_efectivo_insuficiente_se_rechaza():
        venta_id, total, mesa_id, _ = crear_pedido(1)
        espera_error(
            lambda: cobro.cobrar_efectivo(venta_id, total - 1), "no alcanza"
        )
        ps.cancelar_pedido(mesa_id)

    def t06_metodo_de_pago_invalido():
        venta_id, _, mesa_id, _ = crear_pedido(1)
        espera_error(lambda: cobro.cobrar(venta_id, "TARJETA"), "invalido")
        ps.cancelar_pedido(mesa_id)

    def t07_pedido_vacio_no_se_cobra():
        mesa = next(m for m in ps.listar_mesas() if m["estado"] == "DISPONIBLE")
        venta_id = ps.abrir_mesa(mesa["id"])
        espera_error(lambda: cobro.cobrar_efectivo(venta_id, 10000), "productos")
        ps.cancelar_pedido(mesa["id"])

    def t08_doble_cobro_no_duplica():
        venta_id, total, _, _ = crear_pedido(1)
        resumen_antes = cajas.actualizar_totales(estado["caja_id"])
        cobro.cobrar_efectivo(venta_id, total)
        resumen_medio = cajas.actualizar_totales(estado["caja_id"])
        assert resumen_medio["total_general"] == round(
            resumen_antes["total_general"] + total, 2
        )
        espera_error(lambda: cobro.cobrar_efectivo(venta_id, total), "ya fue cobrada")
        resumen_final = cajas.actualizar_totales(estado["caja_id"])
        assert resumen_final["total_general"] == resumen_medio["total_general"], (
            "El cobro duplicado no debe alterar la caja"
        )

    def t09_mesa_liberada_tras_cobro():
        venta_id, total, mesa_id, _ = crear_pedido(1)
        cobro.cobrar_efectivo(venta_id, total)
        mesa = ps.datos_mesa_activa(mesa_id)
        assert mesa["estado"] == "DISPONIBLE"
        assert mesa["venta_activa_id"] is None

    def t10_comprobante_guardado_en_disco():
        venta_id, total, _, producto = crear_pedido(1)
        datos = cobro.cobrar_efectivo(venta_id, total)
        ruta = datos["comprobante_ruta"]
        assert os.path.exists(ruta), f"No se guardo el comprobante: {ruta}"
        with open(ruta, encoding="utf-8") as archivo:
            contenido = archivo.read()
        assert f"#{datos['consecutivo']}" in contenido
        assert producto["nombre"] in contenido
        assert "EFECTIVO" in contenido
        estado.setdefault("comprobantes", []).append(ruta)

    def t11_consecutivos_unicos():
        v1, t1, _, _ = crear_pedido(1)
        v2, t2, _, _ = crear_pedido(1, 1)
        d1 = cobro.cobrar_efectivo(v1, t1)
        d2 = cobro.cobrar_efectivo(v2, t2)
        assert d1["consecutivo"] != d2["consecutivo"]
        estado.setdefault("comprobantes", []).extend(
            [d1["comprobante_ruta"], d2["comprobante_ruta"]]
        )

    def t12_sin_sesion_no_se_puede_cobrar():
        venta_id, total, mesa_id, _ = crear_pedido(1)
        auth_sin = AuthService(db)
        cobro_sin = CobroService(db, auth_sin)
        espera_error(lambda: cobro_sin.cobrar_efectivo(venta_id, total))
        ps.cancelar_pedido(mesa_id)

    def t13_cajero_puede_cobrar():
        usuarios = UsuarioService(db, auth)
        if not db.fetchone("SELECT id FROM usuarios WHERE usuario='cajerop5';"):
            usuarios.crear("Cajero P5", "cajerop5", "clave123", "CAJERO")
        auth_cajero = AuthService(db)
        assert auth_cajero.login("cajerop5", "clave123") is not None
        ps_cajero = PedidoService(db, auth_cajero)
        cobro_cajero = CobroService(db, auth_cajero)
        mesa = next(m for m in ps_cajero.listar_mesas() if m["estado"] == "DISPONIBLE")
        venta_id = ps_cajero.abrir_mesa(mesa["id"])
        producto = ps_cajero.catalogo_productos(True)[0]
        ps_cajero.agregar_producto(venta_id, producto["id"], 1)
        total = ps_cajero.resumen_pedido(venta_id)["total"]
        datos = cobro_cajero.cobrar_efectivo(venta_id, total)
        assert datos["metodo_pago"] == "EFECTIVO"
        assert ps_cajero.datos_mesa_activa(mesa["id"])["estado"] == "DISPONIBLE"
        estado.setdefault("comprobantes", []).append(datos["comprobante_ruta"])

    def t14_cierre_de_caja_con_diferencia():
        resumen = cajas.actualizar_totales(estado["caja_id"])
        contado = round(resumen["efectivo_esperado"] - 1000, 2)
        resultado = cajas.cerrar(estado["caja_id"], contado, "prueba punto 5")
        assert resultado["diferencia"] == 1000, (
            f"diferencia = esperado - contado: {resultado['diferencia']}"
        )
        cierre = db.fetchone(
            "SELECT estado, efectivo_esperado, efectivo_contado, diferencia, "
            "total_efectivo, total_transferencia, total_general, fecha_cierre "
            "FROM cajas WHERE id=?;",
            (estado["caja_id"],),
        )
        assert cierre["estado"] == "CERRADA" and cierre["fecha_cierre"]
        assert cierre["efectivo_contado"] == contado
        assert cierre["diferencia"] == 1000
        assert cierre["total_general"] == resumen["total_general"]
        venta_id, total, mesa_id, _ = crear_pedido(1)
        espera_error(lambda: cobro.cobrar_efectivo(venta_id, total), "caja")
        ps.cancelar_pedido(mesa_id)

    registrar("t01_sin_caja_abierta_no_se_cobra", t01_sin_caja_abierta_no_se_cobra)
    registrar("t02_abrir_caja", t02_abrir_caja)
    registrar("t03_cobro_efectivo_calcula_cambio", t03_cobro_efectivo_calcula_cambio)
    registrar("t04_transferencia_no_suma_al_efectivo", t04_transferencia_no_suma_al_efectivo)
    registrar("t05_efectivo_insuficiente_se_rechaza", t05_efectivo_insuficiente_se_rechaza)
    registrar("t06_metodo_de_pago_invalido", t06_metodo_de_pago_invalido)
    registrar("t07_pedido_vacio_no_se_cobra", t07_pedido_vacio_no_se_cobra)
    registrar("t08_doble_cobro_no_duplica", t08_doble_cobro_no_duplica)
    registrar("t09_mesa_liberada_tras_cobro", t09_mesa_liberada_tras_cobro)
    registrar("t10_comprobante_guardado_en_disco", t10_comprobante_guardado_en_disco)
    registrar("t11_consecutivos_unicos", t11_consecutivos_unicos)
    registrar("t12_sin_sesion_no_se_puede_cobrar", t12_sin_sesion_no_se_puede_cobrar)
    registrar("t13_cajero_puede_cobrar", t13_cajero_puede_cobrar)
    registrar("t14_cierre_de_caja_con_diferencia", t14_cierre_de_caja_con_diferencia)

    db.close()
    for ruta in estado.get("comprobantes", []):
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
    print(" PUNTO 5 VALIDADO COMPLETAMENTE [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()


