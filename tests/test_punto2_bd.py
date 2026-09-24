# ============================================================
#  tests/test_punto2_bd.py
#  Pruebas del PUNTO 2 — Base de datos SQLite
#  Ejecutar desde la raiz del proyecto:
#      python tests/test_punto2_bd.py
#  No requiere PySide6: valida unicamente la capa de datos.
# ============================================================
import os
import sys
import shutil
import sqlite3
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

# Redirigir la base de datos a una carpeta temporal ANTES de
# importar app.database.connection (que lee DB_PATH al importar).
_TMP = tempfile.mkdtemp(prefix="pos_test_p2_")
import app.utils.paths as paths
paths.DB_PATH = os.path.join(_TMP, "pos_test.db")

from app.database.connection import DatabaseConnection
from app.database.migrations import (
    inicializar_base_de_datos,
    verificar_base_de_datos,
    version_actual,
)
from app.database.seeder import ejecutar_seeder
from app.services.auth_service import AuthService
from app.services.caja_service import CajaService
from app.services.mesa_service import MesaService
from app.services.producto_service import ProductoService
from app.services.usuario_service import UsuarioService
from app.services.venta_service import VentaService

# Estado compartido entre pruebas (ids creados en el flujo)
STATE = {}
RESULTADOS = []


def registrar(nombre: str, fn, db):
    """Ejecuta una prueba y registra su resultado."""
    try:
        fn(db)
        RESULTADOS.append((nombre, True, ""))
        print(f"  [ OK ] {nombre}")
    except AssertionError as e:
        RESULTADOS.append((nombre, False, str(e)))
        print(f"  [FALLA] {nombre} -> {e}")
    except Exception as e:  # pragma: no cover
        RESULTADOS.append((nombre, False, f"{type(e).__name__}: {e}"))
        print(f"  [ERROR] {nombre} -> {type(e).__name__}: {e}")


def espera_integridad(fn, *fragmentos: str):
    """
    Ejecuta fn() y exige que SQLite la rechace con sqlite3.IntegrityError
    (cubre UNIQUE, CHECK, FK y RAISE(ABORT) de triggers).
    Opcionalmente valida que el mensaje contenga los fragmentos dados.
    """
    try:
        fn()
    except sqlite3.IntegrityError as e:
        for frag in fragmentos:
            assert frag in str(e), (
                f"La BD rechazo con otro motivo: '{e}' (se esperaba '{frag}')"
            )
        return
    except sqlite3.Error as e:
        raise AssertionError(
            f"Se esperaba sqlite3.IntegrityError y llego {type(e).__name__}: {e}"
        )
    raise AssertionError("La operacion debio ser rechazada por la BD y se permitio")


# ============================================================
#  PRUEBAS
# ============================================================
def t01_tablas_requeridas(db):
    TABLAS = [
        "usuarios", "categorias", "productos", "mesas", "ventas",
        "detalle_ventas", "cajas", "configuracion", "migraciones_bd",
    ]
    existentes = {
        r["name"] for r in db.fetchall(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )
    }
    for tabla in TABLAS:
        assert tabla in existentes, f"Falta la tabla requerida: {tabla}"


def t02_migraciones_versionadas(db):
    assert version_actual(db) >= 3, "Las migraciones v1/v2/v3 no quedaron registradas"
    filas = db.fetchall(
        "SELECT version FROM migraciones_bd ORDER BY version;"
    )
    assert len(filas) == 3, (
        f"Se esperaban 3 migraciones registradas y hay {len(filas)}"
    )


def t03_configuracion_por_defecto(db):
    requeridas = [
        "nombre_negocio", "mensaje_final", "ancho_ticket_mm",
        "consecutivo_actual", "impresora",
    ]
    presentes = {
        r["clave"] for r in db.fetchall("SELECT clave FROM configuracion;")
    }
    for clave in requeridas:
        assert clave in presentes, f"Falta clave de configuracion: {clave}"


def t04_admin_defecto_con_hash(db):
    row = db.fetchone("SELECT * FROM usuarios WHERE usuario='admin';")
    assert row, "No se creo el usuario ADMIN por defecto"
    assert row["rol"] == "ADMIN"
    assert row["activo"] == 1
    assert row["fecha_creacion"], "Falta fecha de creacion"
    assert row["password_hash"].startswith("$2b$"), (
        "La contrasena no esta almacenada con hash bcrypt"
    )
    assert AuthService.verificar_password("admin123", row["password_hash"])
    assert not AuthService.verificar_password("incorrecta", row["password_hash"])


def t05_seeder_idempotente(db):
    res = ejecutar_seeder(db)
    assert res["categorias"] == 0 and res["productos"] == 0 and res["mesas"] == 0, (
        f"El seeder duplico datos al ejecutarse dos veces: {res}"
    )
    n_cat = db.fetchone("SELECT COUNT(*) AS n FROM categorias;")["n"]
    n_prod = db.fetchone("SELECT COUNT(*) AS n FROM productos;")["n"]
    n_mesa = db.fetchone("SELECT COUNT(*) AS n FROM mesas;")["n"]
    assert (n_cat, n_prod, n_mesa) == (6, 24, 12), (
        f"Conteos inesperados: categorias={n_cat}, productos={n_prod}, mesas={n_mesa}"
    )


def t06_productos_sin_stock(db):
    cols = {r["name"] for r in db.fetchall("PRAGMA table_info(productos);")}
    assert "stock" not in cols and "existencias" not in cols, (
        "Los productos NO deben llevar stock de unidades vendibles (regla del Punto 2)"
    )


def t07_usuarios_unicos_y_roles(db):
    svc = UsuarioService(db)
    svc.crear("Cajero Uno", "cajero1", "clave123", "CAJERO")
    # UNIQUE a nivel BD: no puede repetirse el nombre de usuario
    espera_integridad(
        lambda: svc.crear("Otro", "cajero1", "clave999", "CAJERO")
    )
    # CHECK a nivel BD: rol fuera de ADMIN/CAJERO (SQL directo, sin servicio)
    espera_integridad(
        lambda: db.execute(
            "INSERT INTO usuarios (nombre, usuario, password_hash, rol) "
            "VALUES ('Raro', 'usuario_raro', 'hashx', 'SUPERVISOR');"
        )
    )
    row = db.fetchone(
        "SELECT activo, fecha_creacion FROM usuarios WHERE usuario='cajero1';"
    )
    assert row["activo"] == 1 and row["fecha_creacion"]

def t08_flujo_completo_de_ventas(db):
    """
    Valida el nucleo del Punto 2: caja -> venta -> detalles -> cobro,
    con los dos metodos de pago y los totales de caja correctos.
    """
    caja_s = CajaService(db)
    venta_s = VentaService(db)
    mesa_s = MesaService(db)
    prod_s = ProductoService(db)

    admin = db.fetchone("SELECT id FROM usuarios WHERE usuario='admin';")["id"]
    STATE["admin_id"] = admin

    caja1 = caja_s.abrir(admin, 50000.0)
    STATE["caja1"] = caja1

    mesas = {m["nombre"]: m for m in mesa_s.listar()}
    prods = {p["nombre"]: p for p in prod_s.listar_activos()}
    STATE["prod1_id"] = prods["Hamburguesa Sencilla"]["id"]
    STATE["prod2_id"] = prods["Gaseosa Personal"]["id"]
    STATE["prod3_id"] = prods["Combo Personal"]["id"]
    STATE["prod3_precio"] = prods["Combo Personal"]["precio"]
    STATE["cat1_id"] = db.fetchone(
        "SELECT id FROM categorias WHERE nombre='Hamburguesas';"
    )["id"]
    STATE["mesa1_id"] = mesas["Mesa 1"]["id"]
    STATE["mesa3_id"] = mesas["Mesa 3"]["id"]
    STATE["barra_id"] = mesas["Barra"]["id"]

    # ---- Venta 1: EFECTIVO en Mesa 1 ----
    v1 = venta_s.abrir_venta(STATE["mesa1_id"], admin, caja1)
    STATE["v1"] = v1
    mesa_s.ocupar(STATE["mesa1_id"], v1)
    venta_s.agregar_detalle(v1, STATE["prod1_id"], "Hamburguesa Sencilla", 2, 12000)
    venta_s.agregar_detalle(v1, STATE["prod2_id"], "Gaseosa Personal", 1, 3000)
    venta_s.agregar_detalle(v1, STATE["prod1_id"], "Hamburguesa Sencilla", 1, 12000)

    dets = venta_s.obtener_detalles(v1)
    assert len(dets) == 2, (
        "El mismo producto repetido debe agruparse en un solo detalle"
    )
    fila = db.fetchone(
        "SELECT subtotal, total, estado, consecutivo, fecha_hora FROM ventas WHERE id=?;",
        (v1,),
    )
    assert fila["subtotal"] == 39000 and fila["total"] == 39000, (
        f"Totales incorrectos: subtotal={fila['subtotal']}, total={fila['total']}"
    )
    assert fila["estado"] == "ABIERTA"
    assert fila["consecutivo"] == 1, "El consecutivo debe empezar en 1"
    assert fila["fecha_hora"], "La venta debe registrar fecha y hora"
    consec1 = fila["consecutivo"]

    assert venta_s.cobrar(v1, "EFECTIVO") is True
    fila = db.fetchone(
        "SELECT estado, metodo_pago, cobro_procesado FROM ventas WHERE id=?;", (v1,)
    )
    assert (
        fila["estado"] == "CERRADA"
        and fila["metodo_pago"] == "EFECTIVO"
        and fila["cobro_procesado"] == 1
    )
    mesa_s.liberar(STATE["mesa1_id"])

    # ---- Venta 2: TRANSFERENCIA en Mesa 2 ----
    v2 = venta_s.abrir_venta(mesas["Mesa 2"]["id"], admin, caja1)
    STATE["v2"] = v2
    mesa_s.ocupar(mesas["Mesa 2"]["id"], v2)
    venta_s.agregar_detalle(
        v2, prods["Gaseosa Grande"]["id"], "Gaseosa Grande", 1, 5000
    )
    assert venta_s.cobrar(v2, "TRANSFERENCIA") is True
    mesa_s.liberar(mesas["Mesa 2"]["id"])

    consec2 = db.fetchone("SELECT consecutivo FROM ventas WHERE id=?;", (v2,))
    assert consec2["consecutivo"] == consec1 + 1, (
        "El consecutivo debe ser folio secuencial unico"
    )

    # ---- Totales de caja: la transferencia NO suma al efectivo ----
    resumen = caja_s.actualizar_totales(caja1)
    assert resumen["total_efectivo"] == 39000, f"Efectivo: {resumen}"
    assert resumen["total_transferencia"] == 5000, f"Transferencia: {resumen}"
    assert resumen["total_general"] == 44000, f"Total general: {resumen}"
    assert resumen["efectivo_esperado"] == 89000, (
        f"Efectivo esperado = base + efectivo vendido: {resumen}"
    )
    STATE["efectivo_esperado"] = resumen["efectivo_esperado"]

    caja = db.fetchone(
        "SELECT total_efectivo, total_transferencia, total_general "
        "FROM cajas WHERE id=?;",
        (caja1,),
    )
    assert caja["total_efectivo"] == 39000
    assert caja["total_transferencia"] == 5000
    assert caja["total_general"] == 44000

def t09_precios_y_nombres_historicos(db):
    """
    Regla critica del Punto 2: al cambiar precio o nombre de un producto,
    las ventas anteriores conservan el nombre y el precio de ese momento.
    """
    prod_s = ProductoService(db)
    prod1 = STATE["prod1_id"]

    det = db.fetchone(
        "SELECT nombre_producto, precio_unitario, cantidad, subtotal "
        "FROM detalle_ventas WHERE venta_id=? AND producto_id=?;",
        (STATE["v1"], prod1),
    )
    assert det["precio_unitario"] == 12000
    assert det["nombre_producto"] == "Hamburguesa Sencilla"
    assert det["subtotal"] == det["cantidad"] * det["precio_unitario"]

    # Cambiar precio ahora NO altera la venta historica
    prod_s.cambiar_precio(prod1, 13000)
    fila = db.fetchone(
        "SELECT precio, fecha_modificacion, fecha_creacion FROM productos WHERE id=?;",
        (prod1,),
    )
    assert fila["precio"] == 13000
    assert fila["fecha_modificacion"] >= fila["fecha_creacion"], (
        "fecha_modificacion debe actualizarse al cambiar el precio"
    )

    # Cambiar nombre tampoco altera el detalle historico
    prod_s.actualizar(
        prod1, "Hamburguesa Sencilla XL", "desc nueva", STATE["cat1_id"], 13000
    )
    det2 = db.fetchone(
        "SELECT nombre_producto, precio_unitario FROM detalle_ventas "
        "WHERE venta_id=? AND producto_id=?;",
        (STATE["v1"], prod1),
    )
    assert det2["nombre_producto"] == "Hamburguesa Sencilla" and (
        det2["precio_unitario"] == 12000
    ), "El historial debe conservar nombre y precio al momento de la venta"

def t10_proteccion_contra_doble_cobro(db):
    venta_s = VentaService(db)
    assert venta_s.cobrar(STATE["v1"], "TRANSFERENCIA") is False, (
        "No se debe poder cobrar una venta ya cobrada"
    )
    assert venta_s.cobrar(999999, "EFECTIVO") is False


def t11_historial_protegido(db):
    """
    A nivel de BD: las ventas NUNCA se eliminan y una venta cerrada
    queda congelada, igual que su detalle.
    """
    v1 = STATE["v1"]

    # Eliminar ventas: prohibido siempre
    espera_integridad(
        lambda: db.execute("DELETE FROM ventas WHERE id=?;", (v1,)),
        "no se pueden eliminar",
    )

    # Alterar campos de una venta cerrada: prohibido
    casos = [
        ("UPDATE ventas SET total=1 WHERE id=?;", (v1,)),
        ("UPDATE ventas SET subtotal=1 WHERE id=?;", (v1,)),
        ("UPDATE ventas SET descuento=1 WHERE id=?;", (v1,)),
        ("UPDATE ventas SET metodo_pago='TRANSFERENCIA' WHERE id=?;", (v1,)),
        ("UPDATE ventas SET consecutivo=999 WHERE id=?;", (v1,)),
        ("UPDATE ventas SET caja_id=NULL WHERE id=?;", (v1,)),
        ("UPDATE ventas SET fecha_hora='2000-01-01 00:00:00' WHERE id=?;", (v1,)),
        ("UPDATE ventas SET cobro_procesado=0 WHERE id=?;", (v1,)),
    ]
    usuario_otro = db.fetchone(
        "SELECT id FROM usuarios WHERE usuario='cajero1';"
    )["id"]
    casos.append(("UPDATE ventas SET usuario_id=? WHERE id=?;", (usuario_otro, v1)))
    for sql, params in casos:
        espera_integridad(lambda s=sql, p=params: db.execute(s, p), "venta cerrada")

    # La reapertura manual existe (se controla por permisos en el Punto 3)
    db.execute("UPDATE ventas SET estado='ABIERTA' WHERE id=?;", (v1,))
    db.commit()
    db.execute("UPDATE ventas SET estado='CERRADA' WHERE id=?;", (v1,))
    db.commit()

    # Detalle de una venta cerrada: congelado
    det_id = db.fetchone(
        "SELECT id FROM detalle_ventas WHERE venta_id=? LIMIT 1;", (v1,)
    )["id"]
    espera_integridad(
        lambda: db.execute(
            "INSERT INTO detalle_ventas (venta_id, producto_id, nombre_producto, "
            "cantidad, precio_unitario, subtotal) VALUES (?, NULL, 'Hack', 1, 1, 1);",
            (v1,),
        ),
        "venta cerrada",
    )
    espera_integridad(
        lambda: db.execute(
            "UPDATE detalle_ventas SET cantidad=99 WHERE id=?;", (det_id,)
        ),
        "venta cerrada",
    )
    espera_integridad(
        lambda: db.execute("DELETE FROM detalle_ventas WHERE id=?;", (det_id,)),
        "venta cerrada",
    )

    # FK: detalle apuntando a una venta inexistente
    espera_integridad(
        lambda: db.execute(
            "INSERT INTO detalle_ventas (venta_id, producto_id, nombre_producto, "
            "cantidad, precio_unitario, subtotal) VALUES (9999, NULL, 'X', 1, 1, 1);"
        )
    )
    # CHECK: estado fuera de ABIERTA/CERRADA/ANULADA
    espera_integridad(
        lambda: db.execute(
            "INSERT INTO ventas (consecutivo, mesa_id, usuario_id, estado) "
            "VALUES (9999, NULL, ?, 'BORRADOR');",
            (STATE["admin_id"],),
        )
    )

def t12_venta_abierta_sigue_editable(db):
    """
    Los triggers NO deben bloquear el trabajo normal: una venta ABIERTA
    se edita libremente y se anula sin borrarse (el historial no se pierde).
    """
    venta_s = VentaService(db)
    mesa_s = MesaService(db)
    admin = STATE["admin_id"]

    v3 = venta_s.abrir_venta(STATE["mesa3_id"], admin, STATE["caja1"])
    mesa_s.ocupar(STATE["mesa3_id"], v3)
    venta_s.agregar_detalle(v3, STATE["prod2_id"], "Gaseosa Personal", 1, 3000)
    venta_s.agregar_detalle(
        v3, STATE["prod3_id"], "Combo Personal", 1, STATE["prod3_precio"]
    )
    dets = venta_s.obtener_detalles(v3)
    assert len(dets) == 2

    venta_s.actualizar_cantidad_detalle(dets[0]["id"], 3)
    fila = db.fetchone("SELECT subtotal, total FROM ventas WHERE id=?;", (v3,))
    assert fila["subtotal"] == 27000 and fila["total"] == 27000, (
        f"Total recalculado incorrecto: {dict(fila)}"
    )  # 3 x 3000 (gaseosa) + 18000 (combo)

    venta_s.eliminar_detalle(dets[1]["id"])
    fila = db.fetchone("SELECT subtotal, total FROM ventas WHERE id=?;", (v3,))
    assert fila["subtotal"] == 9000 and fila["total"] == 9000

    # Anulacion: la venta no se borra, cambia de estado y queda congelada
    assert venta_s.anular(v3) is True
    fila = db.fetchone("SELECT estado FROM ventas WHERE id=?;", (v3,))
    assert fila["estado"] == "ANULADA"
    mesa_s.liberar(STATE["mesa3_id"])
    espera_integridad(
        lambda: venta_s.agregar_detalle(
            v3, STATE["prod2_id"], "Gaseosa Personal", 1, 3000
        ),
        "venta cerrada",
    )
    assert venta_s.anular(v3) is False, "No debe permitir anular dos veces"


def t13_una_sola_caja_abierta(db):
    """Regla de negocio: solo puede existir UNA caja ABIERTA por jornada."""
    caja_s = CajaService(db)
    espera_integridad(
        lambda: caja_s.abrir(STATE["admin_id"], 10000.0),
    )
    resumen = caja_s.cerrar(
        STATE["caja1"], STATE["efectivo_esperado"], "cierre de prueba"
    )
    assert resumen["efectivo_esperado"] == 89000
    assert resumen["diferencia"] == 0, f"Diferencia debia ser 0: {resumen}"
    fila = db.fetchone(
        "SELECT estado, fecha_cierre, efectivo_contado, diferencia, "
        "total_efectivo, total_transferencia, total_general "
        "FROM cajas WHERE id=?;",
        (STATE["caja1"],),
    )
    assert fila["estado"] == "CERRADA" and fila["fecha_cierre"]
    assert fila["efectivo_contado"] == 89000 and fila["diferencia"] == 0
    assert fila["total_efectivo"] == 39000
    assert fila["total_transferencia"] == 5000
    assert fila["total_general"] == 44000

    # Ahora si se puede abrir la siguiente jornada
    STATE["caja2"] = caja_s.abrir(STATE["admin_id"], 20000.0)
    assert caja_s.caja_abierta()["id"] == STATE["caja2"]

    # Diferencia con signo del enunciado: esperado - contado
    resumen2 = caja_s.cerrar(STATE["caja2"], 19500.0, "faltante de prueba")
    assert resumen2["efectivo_esperado"] == 20000
    assert resumen2["diferencia"] == 500, (
        f"diferencia = esperado - contado (500): {resumen2}"
    )
    assert caja_s.caja_abierta() is None

def t14_integridad_referencial_cajas_y_usuarios(db):
    """FKs activas en el resto del esquema."""
    # Venta con usuario inexistente
    espera_integridad(
        lambda: db.execute(
            "INSERT INTO ventas (consecutivo, usuario_id) VALUES (8888, 99999);"
        )
    )
    # Caja con usuario inexistente
    espera_integridad(
        lambda: db.execute("INSERT INTO cajas (usuario_id) VALUES (99999);")
    )
    # Mesa ocupada apuntando a venta inexistente
    espera_integridad(
        lambda: db.execute(
            "UPDATE mesas SET venta_activa_id=99999 WHERE id=?;",
            (STATE["mesa1_id"],),
        )
    )
    # Producto con categoria inexistente
    espera_integridad(
        lambda: db.execute(
            "INSERT INTO productos (nombre, categoria_id, precio) "
            "VALUES ('Fantasma', 99999, 1000);"
        )
    )


def t15_consultas_historicas(db):
    """El historial queda consultable con filtros basicos (Punto 7 lo amplia)."""
    venta_s = VentaService(db)
    todas = venta_s.listar_con_filtros()
    assert len(todas) == 2, f"Deben existir 2 ventas cerradas: {len(todas)}"
    solo_transf = venta_s.listar_con_filtros(metodo_pago="TRANSFERENCIA")
    assert len(solo_transf) == 1 and solo_transf[0]["metodo_pago"] == "TRANSFERENCIA"
    por_usuario = venta_s.listar_con_filtros(usuario_id=STATE["admin_id"])
    assert len(por_usuario) == 2
    historial_cajas = CajaService(db).historial()
    assert len(historial_cajas) == 2, "Deben existir 2 jornadas de caja cerradas"
    # Los detalles de la venta anulada siguen consultables (historial completo)
    anuladas = db.fetchall("SELECT id FROM ventas WHERE estado='ANULADA';")
    assert len(anuladas) == 1 and anuladas[0]["id"] == 3


def t16_verificacion_e_integridad_bd(db):
    """verificar_base_de_datos() debe reportar el esquema sano."""
    reporte = verificar_base_de_datos(db)
    assert reporte["ok"], f"Integridad reporto fallos: {reporte}"
    assert reporte["integridad"] == "ok"
    assert reporte["claves_foraneas"] == 0, (
        f"Violaciones de FK: {reporte['claves_foraneas']}"
    )
    assert reporte["version"] >= 2


# ============================================================
#  MAIN
# ============================================================
PRUEBAS = [
    t01_tablas_requeridas,
    t02_migraciones_versionadas,
    t03_configuracion_por_defecto,
    t04_admin_defecto_con_hash,
    t05_seeder_idempotente,
    t06_productos_sin_stock,
    t07_usuarios_unicos_y_roles,
    t08_flujo_completo_de_ventas,
    t09_precios_y_nombres_historicos,
    t10_proteccion_contra_doble_cobro,
    t11_historial_protegido,
    t12_venta_abierta_sigue_editable,
    t13_una_sola_caja_abierta,
    t14_integridad_referencial_cajas_y_usuarios,
    t15_consultas_historicas,
    t16_verificacion_e_integridad_bd,
]


def main():
    db = DatabaseConnection()
    inicializar_base_de_datos(db)
    ejecutar_seeder(db)  # idempotente: no duplica

    print("=" * 60)
    print(" PRUEBAS PUNTO 2 — BASE DE DATOS SQLITE")
    print("=" * 60)

    for fn in PRUEBAS:
        registrar(fn.__name__, fn, db)

    db.close()
    print("-" * 60)
    ok = sum(1 for _, exito, _ in RESULTADOS if exito)
    print(f" RESULTADO: {ok}/{len(RESULTADOS)} pruebas exitosas")
    fallos = [n for n, exito, _ in RESULTADOS if not exito]
    if fallos:
        print(" Fallaron:", ", ".join(fallos))
        sys.exit(1)
    print(" PUNTO 2 VALIDADO COMPLETAMENTE [OK]")
    shutil.rmtree(_TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
