# -*- coding: utf-8 -*-
"""Pruebas del PUNTO 7 - Historial permanente de ventas (sin PySide6)."""
import os
import sys
import shutil
import sqlite3
import tempfile
from datetime import date, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_TMP = tempfile.mkdtemp(prefix="p7test_")
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
from app.services.venta_service import VentaService
from app.services.comprobante_service import ComprobanteService

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
    cajas = CajaService(db, auth)
    cajas.abrir(auth.usuario_actual.id, 0)

    # Cajero adicional para probar el filtro por cajero
    usuarios = UsuarioService(db, auth)
    if not db.fetchone("SELECT id FROM usuarios WHERE usuario='cajerop7';"):
        usuarios.crear("Cajero Siete", "cajerop7", "clave123", "CAJERO")
    auth_cajero = AuthService(db)
    assert auth_cajero.login("cajerop7", "clave123") is not None

    ps_admin = PedidoService(db, auth)
    ps_cajero = PedidoService(db, auth_cajero)
    cobro = CobroService(db, auth)
    cobro_cajero = CobroService(db, auth_cajero)
    ventas = VentaService(db, auth)
    estado = {"ventas": []}

    def cobrar(mesa_id, venta_id, metodo, servicio_cobro):
        total = db.fetchone("SELECT total FROM ventas WHERE id=?;", (venta_id,))["total"]
        if metodo == "EFECTIVO":
            servicio_cobro.cobrar_efectivo(venta_id, total)
        else:
            servicio_cobro.cobrar_transferencia(venta_id)

    def abrir_en(nombre_mesa, servicio):
        """Abre una mesa por nombre exacto y retorna (venta_id, mesa_id)."""
        mesa = next(
            m for m in servicio.listar_mesas() if m["nombre"] == nombre_mesa
        )
        venta_id = servicio.abrir_mesa(mesa["id"])
        return venta_id, mesa["id"]

    def preparar_ventas():
        # v1: admin, Barra, EFECTIVO, prod0 x2
        v1, m1 = abrir_en("Barra", ps_admin)
        p = ps_admin.catalogo_productos(True)[0]
        ps_admin.agregar_producto(v1, p["id"], 2)
        cobrar(m1, v1, "EFECTIVO", cobro)
        # v2: admin, Mesa 1, TRANSFERENCIA, prod1 x1
        v2, m2 = abrir_en("Mesa 1", ps_admin)
        p = ps_admin.catalogo_productos(True)[1]
        ps_admin.agregar_producto(v2, p["id"], 1)
        cobrar(m2, v2, "TRANSFERENCIA", cobro)
        # v3: cajero, Barra (mismo fisico), EFECTIVO, prod2 x3
        v3, m3 = abrir_en("Barra", ps_cajero)
        p = ps_cajero.catalogo_productos(True)[2]
        ps_cajero.agregar_producto(v3, p["id"], 3)
        cobrar(m3, v3, "EFECTIVO", cobro_cajero)
        # v4: cajero, Mesa 2, TRANSFERENCIA, prod0 x1
        v4, m4 = abrir_en("Mesa 2", ps_cajero)
        p = ps_cajero.catalogo_productos(True)[0]
        ps_cajero.agregar_producto(v4, p["id"], 1)
        cobrar(m4, v4, "TRANSFERENCIA", cobro_cajero)

        estado["ventas"] = [v1, v2, v3, v4]
        estado["v1"], estado["v2"], estado["v3"], estado["v4"] = v1, v2, v3, v4
        filas = db.fetchall("SELECT id, mesa_id, usuario_id, consecutivo, metodo_pago "
                            "FROM ventas ORDER BY id;")
        estado["filas"] = filas

    preparar_ventas()
    HOY = date.today().isoformat()
    AYER = (date.today() - timedelta(days=1)).isoformat()
    MANANA = (date.today() + timedelta(days=1)).isoformat()

    def t01_historial_completo_para_admin():
        filas = ventas.listar_con_filtros()
        assert len(filas) == 4, f"Se esperaban 4 ventas: {len(filas)}"
        consecutivos = sorted(f["consecutivo"] for f in filas)
        assert consecutivos == [1, 2, 3, 4]
        assert all(f["estado"] == "CERRADA" for f in filas)

    def t02_filtro_por_consecutivo():
        fila = ventas.listar_con_filtros(consecutivo=2)
        assert len(fila) == 1
        assert fila[0]["id"] == estado["v2"]
        assert fila[0]["metodo_pago"] == "TRANSFERENCIA"

    def t03_filtro_fecha_exacta():
        filas = ventas.listar_con_filtros(desde=HOY, hasta=HOY)
        assert len(filas) == 4, f"Todas son de hoy: {len(filas)}"
        assert ventas.listar_con_filtros(desde=MANANA, hasta=MANANA) == []

    def t04_filtro_rango_de_fechas():
        filas = ventas.listar_con_filtros(desde=AYER, hasta=MANANA)
        assert len(filas) == 4
        assert ventas.listar_con_filtros(desde=AYER, hasta=AYER) == []
        assert ventas.listar_con_filtros(desde=MANANA) == []

    def t05_filtro_por_mesa():
        mesa_v1 = db.fetchone(
            "SELECT mesa_id FROM ventas WHERE id=?;", (estado["v1"],)
        )["mesa_id"]
        filas = ventas.listar_con_filtros(mesa_id=mesa_v1)
        assert len(filas) == 2, f"La mesa 1 tuvo 2 ventas: {len(filas)}"
        assert all(f["mesa_id"] == mesa_v1 for f in filas)

    def t06_filtro_por_cajero():
        cajero_id = db.fetchone(
            "SELECT usuario_id FROM ventas WHERE id=?;", (estado["v3"],)
        )["usuario_id"]
        filas = ventas.listar_con_filtros(usuario_id=cajero_id)
        assert len(filas) == 2
        assert {f["id"] for f in filas} == {estado["v3"], estado["v4"]}

    def t07_filtro_por_metodo_de_pago():
        efectivo = ventas.listar_con_filtros(metodo_pago="EFECTIVO")
        transferencia = ventas.listar_con_filtros(metodo_pago="TRANSFERENCIA")
        assert len(efectivo) == 2 and len(transferencia) == 2
        assert all(f["metodo_pago"] == "EFECTIVO" for f in efectivo)
        assert all(f["metodo_pago"] == "TRANSFERENCIA" for f in transferencia)

    def t08_filtros_combinados():
        mesa_v1 = db.fetchone(
            "SELECT mesa_id FROM ventas WHERE id=?;", (estado["v1"],)
        )["mesa_id"]
        admin_id = db.fetchone(
            "SELECT usuario_id FROM ventas WHERE id=?;", (estado["v1"],)
        )["usuario_id"]
        filas = ventas.listar_con_filtros(
            mesa_id=mesa_v1, usuario_id=admin_id, metodo_pago="EFECTIVO"
        )
        assert len(filas) == 1
        assert filas[0]["id"] == estado["v1"]

    def t09_detalle_completo_de_la_venta():
        venta = ventas.obtener_por_id(estado["v1"])
        assert venta["consecutivo"] == 1
        assert venta["estado"] == "CERRADA"
        assert venta["usuario_nombre"] == "Administrador"
        assert venta["mesa_nombre"], "Debe tener nombre de mesa"
        detalles = ventas.obtener_detalles(estado["v1"])
        assert len(detalles) == 1
        d = detalles[0]
        assert d["cantidad"] == 2
        assert d["subtotal"] == d["cantidad"] * d["precio_unitario"]
        resumen_total = sum(x["subtotal"] for x in detalles)
        assert venta["total"] == resumen_total

    def t10_reimpresion_desde_el_historial():
        """Reimprimir n veces no cambia la venta ni la caja."""
        comprobante = ComprobanteService(db)
        texto1 = comprobante.generar_texto(estado["v1"])
        caja_id = db.fetchone("SELECT id FROM cajas WHERE estado='ABIERTA';")["id"]
        resumen_antes = cajas.actualizar_totales(caja_id)
        for _ in range(3):
            ok, _ = cobro.imprimir_comprobante(estado["v1"])
            assert ok is False  # sin impresora configurada: fallo suave
        assert comprobante.generar_texto(estado["v1"]) == texto1
        resumen_despues = cajas.actualizar_totales(caja_id)
        assert resumen_despues["total_general"] == resumen_antes["total_general"]

    def t11_historial_persiste_tras_reinicio():
        """Una conexion nueva al archivo ve el mismo historial (simula reinicio)."""
        conexion = sqlite3.connect(paths.DB_PATH)
        try:
            filas = conexion.execute(
                "SELECT COUNT(*) FROM ventas WHERE estado='CERRADA';"
            ).fetchone()[0]
            total_general = conexion.execute(
                "SELECT COALESCE(SUM(total),0) FROM ventas WHERE estado='CERRADA';"
            ).fetchone()[0]
        finally:
            conexion.close()
        assert filas == 4
        assert total_general == 30500, f"Total historico: {total_general}"

    def t12_cajero_ve_solo_sus_ventas():
        servicio_cajero = VentaService(db, auth_cajero)
        propias = servicio_cajero.listar_con_filtros()
        assert len(propias) == 2
        assert {f["id"] for f in propias} == {estado["v3"], estado["v4"]}

    def t13_sin_sesion_no_consulta_historial():
        auth_sin = AuthService(db)
        servicio_sin = VentaService(db, auth_sin)
        try:
            servicio_sin.listar_con_filtros()
            raise AssertionError("Sin sesion debio negarse")
        except PermissionError:
            pass

    def t14_historial_nunca_se_elimina():
        """La BD rechaza borrar ventas (historial permanente)."""
        try:
            db.execute("DELETE FROM ventas WHERE id=?;", (estado["v1"],))
            raise AssertionError("La BD debio bloquear el borrado de ventas")
        except Exception as e:
            assert "no se pueden eliminar" in str(e)
        assert len(ventas.listar_con_filtros()) == 4

    registrar("t01_historial_completo_para_admin", t01_historial_completo_para_admin)
    registrar("t02_filtro_por_consecutivo", t02_filtro_por_consecutivo)
    registrar("t03_filtro_fecha_exacta", t03_filtro_fecha_exacta)
    registrar("t04_filtro_rango_de_fechas", t04_filtro_rango_de_fechas)
    registrar("t05_filtro_por_mesa", t05_filtro_por_mesa)
    registrar("t06_filtro_por_cajero", t06_filtro_por_cajero)
    registrar("t07_filtro_por_metodo_de_pago", t07_filtro_por_metodo_de_pago)
    registrar("t08_filtros_combinados", t08_filtros_combinados)
    registrar("t09_detalle_completo_de_la_venta", t09_detalle_completo_de_la_venta)
    registrar("t10_reimpresion_desde_el_historial", t10_reimpresion_desde_el_historial)
    registrar("t11_historial_persiste_tras_reinicio", t11_historial_persiste_tras_reinicio)
    registrar("t12_cajero_ve_solo_sus_ventas", t12_cajero_ve_solo_sus_ventas)
    registrar("t13_sin_sesion_no_consulta_historial", t13_sin_sesion_no_consulta_historial)
    registrar("t14_historial_nunca_se_elimina", t14_historial_nunca_se_elimina)

    db.close()
    print("-" * 60)
    ok = sum(1 for _, exito, _ in RESULTADOS if exito)
    print(f" RESULTADO: {ok}/{len(RESULTADOS)} pruebas exitosas")
    fallos = [n for n, exito, _ in RESULTADOS if not exito]
    if fallos:
        print(" Fallaron:", ", ".join(fallos))
        sys.exit(1)
    print(" PUNTO 7 VALIDADO COMPLETAMENTE [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()


