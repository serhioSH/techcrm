# -*- coding: utf-8 -*-
"""Pruebas del PUNTO 4 - Mesas y pedidos (sin PySide6)."""
import os
import sys
import shutil
import sqlite3
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_TMP = tempfile.mkdtemp(prefix="p4test_")
import app.utils.paths as paths
paths.DB_PATH = os.path.join(_TMP, "pos.db")

from app.database.connection import DatabaseConnection
from app.database.migrations import inicializar_base_de_datos
from app.database.seeder import ejecutar_seeder
from app.services.auth_service import AuthService
from app.services.pedido_service import PedidoService

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
    db = DatabaseConnection()
    inicializar_base_de_datos(db)
    ejecutar_seeder(db)
    auth = AuthService(db)
    assert auth.login("admin", "admin123") is not None
    ps = PedidoService(db, auth)
    estado = {}

    def t01_carga_inicial():
        mesas = ps.listar_mesas()
        assert len(mesas) == 12, f"Se esperaban 12 mesas: {len(mesas)}"
        assert all(m["estado"] == "DISPONIBLE" for m in mesas)
        assert all(m["venta_activa_id"] is None for m in mesas)
        assert len(ps.catalogo_productos(solo_activos=True)) == 24

    def t02_abrir_mesa():
        mesa = ps.listar_mesas()[0]
        venta_id = ps.abrir_mesa(mesa["id"])
        assert venta_id > 0
        m = ps.datos_mesa_activa(mesa["id"])
        assert m["estado"] == "OCUPADA"
        assert m["venta_activa_id"] == venta_id
        estado["mesa_id"] = mesa["id"]
        estado["venta_id"] = venta_id

    def t03_no_reabrir_mesa_ocupada():
        try:
            ps.abrir_mesa(estado["mesa_id"])
            raise AssertionError("Debio rechazar abrir una mesa ya ocupada")
        except ValueError:
            pass

    def t04_agregar_producto_y_total():
        producto = ps.catalogo_productos(True)[0]
        estado["producto"] = producto
        ps.agregar_producto(estado["venta_id"], producto["id"], 2)
        detalles = ps.detalles_pedido(estado["venta_id"])
        assert len(detalles) == 1
        d = detalles[0]
        assert d["cantidad"] == 2
        assert d["precio_unitario"] == producto["precio"]
        assert d["nombre_producto"] == producto["nombre"]
        resumen = ps.resumen_pedido(estado["venta_id"])
        assert resumen["total"] == producto["precio"] * 2

    def t05_agrupa_mismo_producto():
        ps.agregar_producto(estado["venta_id"], estado["producto"]["id"], 1)
        detalles = ps.detalles_pedido(estado["venta_id"])
        assert len(detalles) == 1
        assert detalles[0]["cantidad"] == 3

    def t06_modificar_cantidad_recalcula():
        detalle = ps.detalles_pedido(estado["venta_id"])[0]
        ps.modificar_cantidad(estado["venta_id"], detalle["id"], 5)
        resumen = ps.resumen_pedido(estado["venta_id"])
        assert resumen["total"] == estado["producto"]["precio"] * 5

    def t07_quitar_producto():
        detalle = ps.detalles_pedido(estado["venta_id"])[0]
        ps.quitar_producto(estado["venta_id"], detalle["id"])
        assert ps.detalles_pedido(estado["venta_id"]) == []
        assert ps.resumen_pedido(estado["venta_id"])["total"] == 0

    def t08_usuario_y_estado_del_pedido():
        resumen = ps.resumen_pedido(estado["venta_id"])
        assert resumen["venta"]["usuario_nombre"] == "Administrador"
        assert resumen["venta"]["estado"] == "ABIERTA"

    def t09_pedido_persiste_en_disco():
        """El pedido abierto queda guardado en SQLite (otra conexion al archivo)."""
        ps.agregar_producto(estado["venta_id"], estado["producto"]["id"], 1)
        esperado = ps.resumen_pedido(estado["venta_id"])["total"]
        conexion = sqlite3.connect(paths.DB_PATH)
        try:
            total_venta = conexion.execute(
                "SELECT total FROM ventas WHERE id=?;", (estado["venta_id"],)
            ).fetchone()[0]
            estado_mesa = conexion.execute(
                "SELECT estado FROM mesas WHERE id=?;", (estado["mesa_id"],)
            ).fetchone()[0]
        finally:
            conexion.close()
        assert total_venta == esperado
        assert estado_mesa == "OCUPADA"

    def t10_cancelar_pedido_libera_mesa():
        ps.cancelar_pedido(estado["mesa_id"])
        m = ps.datos_mesa_activa(estado["mesa_id"])
        assert m["estado"] == "DISPONIBLE"
        assert m["venta_activa_id"] is None
        fila = db.fetchone(
            "SELECT estado FROM ventas WHERE id=?;", (estado["venta_id"],)
        )
        assert fila["estado"] == "ANULADA", "la venta no se borra: se anula"

    def t11_mesa_se_puede_reabrir_tras_cancelar():
        mesa = ps.datos_mesa_activa(estado["mesa_id"])
        venta_id = ps.abrir_mesa(mesa["id"])
        assert venta_id != estado["venta_id"]
        assert ps.datos_mesa_activa(mesa["id"])["estado"] == "OCUPADA"
        ps.cancelar_pedido(mesa["id"])

    def t12_pedido_sobrevive_al_reinicio():
        """Otro servicio (como al reiniciar la app) ve el pedido abierto intacto."""
        mesa = [m for m in ps.listar_mesas() if m["estado"] == "DISPONIBLE"][0]
        venta_id = ps.abrir_mesa(mesa["id"])
        producto = ps.catalogo_productos(True)[1]
        ps.agregar_producto(venta_id, producto["id"], 3)

        otro = PedidoService(db, auth)
        resumen = otro.resumen_pedido(venta_id)
        assert resumen["total"] == producto["precio"] * 3
        assert resumen["venta"]["estado"] == "ABIERTA"
        assert otro.datos_mesa_activa(mesa["id"])["venta_activa_id"] == venta_id
        otro.cancelar_pedido(mesa["id"])

    def t13_sin_sesion_no_se_puede_abrir():
        auth_sin = AuthService(db)
        servicio_sin = PedidoService(db, auth_sin)
        mesa = [m for m in servicio_sin.listar_mesas() if m["estado"] == "DISPONIBLE"][0]
        try:
            servicio_sin.abrir_mesa(mesa["id"])
            raise AssertionError("Sin sesion debio negarse (PermissionError)")
        except PermissionError:
            pass

    registrar("t01_carga_inicial", t01_carga_inicial)
    registrar("t02_abrir_mesa", t02_abrir_mesa)
    registrar("t03_no_reabrir_mesa_ocupada", t03_no_reabrir_mesa_ocupada)
    registrar("t04_agregar_producto_y_total", t04_agregar_producto_y_total)
    registrar("t05_agrupa_mismo_producto", t05_agrupa_mismo_producto)
    registrar("t06_modificar_cantidad_recalcula", t06_modificar_cantidad_recalcula)
    registrar("t07_quitar_producto", t07_quitar_producto)
    registrar("t08_usuario_y_estado_del_pedido", t08_usuario_y_estado_del_pedido)
    registrar("t09_pedido_persiste_en_disco", t09_pedido_persiste_en_disco)
    registrar("t10_cancelar_pedido_libera_mesa", t10_cancelar_pedido_libera_mesa)
    registrar("t11_mesa_se_puede_reabrir_tras_cancelar", t11_mesa_se_puede_reabrir_tras_cancelar)
    registrar("t12_pedido_sobrevive_al_reinicio", t12_pedido_sobrevive_al_reinicio)
    registrar("t13_sin_sesion_no_se_puede_abrir", t13_sin_sesion_no_se_puede_abrir)

    db.close()
    print("-" * 60)
    ok = sum(1 for _, exito, _ in RESULTADOS if exito)
    print(f" RESULTADO: {ok}/{len(RESULTADOS)} pruebas exitosas")
    fallos = [n for n, exito, _ in RESULTADOS if not exito]
    if fallos:
        print(" Fallaron:", ", ".join(fallos))
        sys.exit(1)
    print(" PUNTO 4 VALIDADO COMPLETAMENTE [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()

