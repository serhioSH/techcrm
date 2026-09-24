# ============================================================
#  app/database/migrations.py
#  Inicializacion y migraciones versionadas del esquema SQLite
# ============================================================
from app.database.connection import DatabaseConnection


SCHEMA_SQL = """
-- -------------------------------------------------------
-- TABLA: migraciones_bd (control de version del esquema)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS migraciones_bd (
    version         INTEGER PRIMARY KEY,
    descripcion     TEXT    NOT NULL,
    fecha_aplicada  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- -------------------------------------------------------
-- TABLA: usuarios
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL,
    usuario         TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    rol             TEXT    NOT NULL CHECK(rol IN ('ADMIN','CAJERO','TECNICO')),
    activo          INTEGER NOT NULL DEFAULT 1,
    fecha_creacion  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- -------------------------------------------------------
-- TABLA: categorias
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorias (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT    NOT NULL UNIQUE
);

-- -------------------------------------------------------
-- TABLA: productos
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS productos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre              TEXT    NOT NULL,
    descripcion         TEXT,
    categoria_id        INTEGER REFERENCES categorias(id),
    precio              REAL    NOT NULL CHECK(precio >= 0),
    activo              INTEGER NOT NULL DEFAULT 1,
    fecha_creacion      TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    fecha_modificacion  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- -------------------------------------------------------
-- TABLA: mesas
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS mesas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL UNIQUE,
    estado          TEXT    NOT NULL DEFAULT 'DISPONIBLE'
                            CHECK(estado IN ('DISPONIBLE','OCUPADA')),
    tipo            TEXT    NOT NULL DEFAULT 'MESA'
                            CHECK(tipo IN ('MESA','DOMICILIO'))
);

-- -------------------------------------------------------
-- TABLA: cajas
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS cajas (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id              INTEGER NOT NULL REFERENCES usuarios(id),
    fecha_apertura          TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    monto_inicial           REAL    NOT NULL DEFAULT 0,
    fecha_cierre            TEXT,
    efectivo_esperado       REAL,
    efectivo_contado        REAL,
    diferencia              REAL,
    total_efectivo          REAL    NOT NULL DEFAULT 0,
    total_transferencia     REAL    NOT NULL DEFAULT 0,
    total_general           REAL    NOT NULL DEFAULT 0,
    observaciones           TEXT,
    estado                  TEXT    NOT NULL DEFAULT 'ABIERTA'
                                    CHECK(estado IN ('ABIERTA','CERRADA'))
);

-- VENTAS TABLE: mesa_id has NO FK anymore (Migration V6)
CREATE TABLE IF NOT EXISTS ventas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    consecutivo         INTEGER NOT NULL UNIQUE,
    mesa_id             INTEGER,
    usuario_id          INTEGER NOT NULL REFERENCES usuarios(id),
    caja_id             INTEGER REFERENCES cajas(id),
    fecha_hora          TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    subtotal            REAL    NOT NULL DEFAULT 0,
    descuento           REAL    NOT NULL DEFAULT 0,
    total               REAL    NOT NULL DEFAULT 0,
    metodo_pago         TEXT    CHECK(metodo_pago IN ('EFECTIVO','TRANSFERENCIA',NULL)),
    estado              TEXT    NOT NULL DEFAULT 'ABIERTA'
                                CHECK(estado IN ('ABIERTA','CERRADA','ANULADA')),
    cobro_procesado     INTEGER NOT NULL DEFAULT 0,
    cliente             TEXT,
    direccion_entrega   TEXT
);

-- -------------------------------------------------------
-- TABLA: detalle_ventas
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS detalle_ventas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id        INTEGER NOT NULL REFERENCES ventas(id),
    producto_id     INTEGER REFERENCES productos(id),
    nombre_producto TEXT    NOT NULL,
    cantidad        REAL    NOT NULL CHECK(cantidad > 0),
    precio_unitario REAL    NOT NULL CHECK(precio_unitario >= 0),
    subtotal        REAL    NOT NULL
);

-- -------------------------------------------------------
-- TABLA: configuracion
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS configuracion (
    clave   TEXT PRIMARY KEY,
    valor   TEXT
);

-- -------------------------------------------------------
-- INDICES para consultas frecuentes
-- -------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_ventas_fecha     ON ventas(fecha_hora);
CREATE INDEX IF NOT EXISTS idx_ventas_estado    ON ventas(estado);
CREATE INDEX IF NOT EXISTS idx_ventas_caja      ON ventas(caja_id);
CREATE INDEX IF NOT EXISTS idx_detalle_venta    ON detalle_ventas(venta_id);
CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo);
CREATE INDEX IF NOT EXISTS idx_mesas_estado     ON mesas(estado);
-- -------------------------------------------------------
-- TRIGGERS para mantener integridad de datos
-- -------------------------------------------------------

-- Al cerrar una venta, asegurarse de que tiene al menos un detalle
CREATE TRIGGER IF NOT EXISTS trg_venta_cerrar_validar
BEFORE UPDATE ON ventas
FOR EACH ROW
WHEN NEW.estado = 'CERRADA' AND OLD.estado = 'ABIERTA'
BEGIN
    SELECT CASE
        WHEN (SELECT COUNT(*) FROM detalle_ventas WHERE venta_id = NEW.id) = 0
        THEN RAISE(ABORT, 'No se puede cerrar una venta sin productos.')
    END;
END;

-- Actualizar fecha_modificacion de productos al cambiar precio
CREATE TRIGGER IF NOT EXISTS trg_producto_fecha_mod
AFTER UPDATE OF precio ON productos
FOR EACH ROW
BEGIN
    UPDATE productos
    SET fecha_modificacion = datetime('now','localtime')
    WHERE id = OLD.id;
END;

-- Indices adicionales para historial y reportes
CREATE INDEX IF NOT EXISTS idx_ventas_metodo_pago ON ventas(metodo_pago);
CREATE INDEX IF NOT EXISTS idx_ventas_usuario     ON ventas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_ventas_mesa        ON ventas(mesa_id);
CREATE INDEX IF NOT EXISTS idx_ventas_consec      ON ventas(consecutivo);
CREATE INDEX IF NOT EXISTS idx_detalle_producto   ON detalle_ventas(producto_id);
"""

# ============================================================
# MIGRACION v2 — Integridad del negocio y proteccion del historial
# (requisitos del Punto 2 del PROYECTO.md):
#   * Las ventas NUNCA se eliminan: se anulan cambiando su estado.
#   * Una venta cerrada/anulada queda congelada (comprobante historico),
#     igual que su detalle con precios del momento de la venta.
#   * Solo puede existir UNA caja ABIERTA a la vez.
# ============================================================
MIGRACION_V2_SQL = """
-- Estado anomalo heredado: mas de una caja abierta. Se cierra la mas
-- antigua para poder garantizar unicidad a partir de ahora (no-op en BD nuevas).
UPDATE cajas
   SET estado = 'CERRADA',
       fecha_cierre = datetime('now','localtime')
 WHERE estado = 'ABIERTA'
   AND id NOT IN (
       SELECT id FROM cajas WHERE estado = 'ABIERTA'
       ORDER BY fecha_apertura DESC, id DESC LIMIT 1
   );

-- Regla de negocio: una sola caja abierta por jornada
CREATE UNIQUE INDEX IF NOT EXISTS idx_cajas_unica_abierta
    ON cajas (estado)
 WHERE estado = 'ABIERTA';

-- -------------------------------------------------------
-- PROTECCION PERMANENTE DEL HISTORIAL
-- -------------------------------------------------------
-- Las ventas jamas se eliminan (ni por antiguedad ni por accidente)
CREATE TRIGGER IF NOT EXISTS trg_ventas_no_eliminar
BEFORE DELETE ON ventas
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: las ventas no se pueden eliminar, se deben anular.');
END;

-- Una venta cerrada/anulada queda congelada como comprobante historico
CREATE TRIGGER IF NOT EXISTS trg_ventas_cerrada_congelada
BEFORE UPDATE ON ventas
FOR EACH ROW
WHEN OLD.estado IN ('CERRADA', 'ANULADA')
 AND (   NEW.consecutivo      !=  OLD.consecutivo
      OR NEW.mesa_id          IS NOT OLD.mesa_id
      OR NEW.usuario_id       !=  OLD.usuario_id
      OR NEW.caja_id          IS NOT OLD.caja_id
      OR NEW.fecha_hora       !=  OLD.fecha_hora
      OR NEW.subtotal         !=  OLD.subtotal
      OR NEW.descuento        !=  OLD.descuento
      OR NEW.total            !=  OLD.total
      OR NEW.metodo_pago      IS NOT OLD.metodo_pago
      OR NEW.cobro_procesado  !=  OLD.cobro_procesado )
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: una venta cerrada no se puede alterar.');
END;

-- El detalle solo se puede editar mientras la venta esta ABIERTA
CREATE TRIGGER IF NOT EXISTS trg_detalle_no_agregar_cerrada
BEFORE INSERT ON detalle_ventas
FOR EACH ROW
WHEN (SELECT estado FROM ventas WHERE id = NEW.venta_id) != 'ABIERTA'
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: no se pueden agregar productos a una venta cerrada.');
END;

CREATE TRIGGER IF NOT EXISTS trg_detalle_no_modificar_cerrada
BEFORE UPDATE ON detalle_ventas
FOR EACH ROW
WHEN (SELECT estado FROM ventas WHERE id = OLD.venta_id) != 'ABIERTA'
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: el detalle de una venta cerrada no se puede modificar.');
END;

CREATE TRIGGER IF NOT EXISTS trg_detalle_no_eliminar_cerrada
BEFORE DELETE ON detalle_ventas
FOR EACH ROW
WHEN (SELECT estado FROM ventas WHERE id = OLD.venta_id) != 'ABIERTA'
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: el detalle de una venta cerrada no se puede eliminar.');
END;
"""


# ============================================================
# MIGRACION v3 — Eliminar el NIT de la configuracion
# (el negocio es un restaurante local y no lo necesita)
# ============================================================
MIGRACION_V3_SQL = """
DELETE FROM configuracion WHERE clave IN ('nit', 'mostrar_nit');
"""


# ============================================================
# MIGRACION v4 — Mesas de DOMICILIO y datos de entrega
#   * mesas.tipo: MESA (salon) o DOMICILIO (entrega a casa)
#   * ventas.cliente / ventas.direccion_entrega (solo domicilio)
#   * La mesa "Para llevar" pasa a ser "Domicilio 1"
# ============================================================
MIGRACION_V4_SQL = """
CREATE INDEX IF NOT EXISTS idx_mesas_tipo ON mesas(tipo);
UPDATE mesas SET nombre = 'Domicilio 1', tipo = 'DOMICILIO'
 WHERE nombre = 'Para llevar';
"""


# ============================================================
# MIGRACION v5 — Optimizacion para bajo consumo de recursos
#   * Indices compuestos para consultas frecuentes en reportes
#   * Optimizacion de consultas de historial
#   * Mejora de rendimiento en computadores con pocos recursos
# ============================================================
MIGRACION_V5_SQL = """
-- Indices compuestos para reportes (reducen escaneos completos)
CREATE INDEX IF NOT EXISTS idx_ventas_estado_fecha 
    ON ventas(estado, fecha_hora) 
    WHERE estado = 'CERRADA';

CREATE INDEX IF NOT EXISTS idx_ventas_estado_metodo_fecha 
    ON ventas(estado, metodo_pago, fecha_hora) 
    WHERE estado = 'CERRADA';

CREATE INDEX IF NOT EXISTS idx_ventas_caja_estado 
    ON ventas(caja_id, estado) 
    WHERE estado = 'CERRADA';

CREATE INDEX IF NOT EXISTS idx_ventas_usuario_estado_fecha 
    ON ventas(usuario_id, estado, fecha_hora) 
    WHERE estado = 'CERRADA';

CREATE INDEX IF NOT EXISTS idx_ventas_mesa_estado_fecha 
    ON ventas(mesa_id, estado, fecha_hora) 
    WHERE estado = 'CERRADA';

-- Indice para detalle de ventas en reportes
CREATE INDEX IF NOT EXISTS idx_detalle_venta_producto 
    ON detalle_ventas(venta_id, producto_id, nombre_producto);

-- Indice para productos activos por categoria
CREATE INDEX IF NOT EXISTS idx_productos_categoria_activo 
    ON productos(categoria_id, activo) 
    WHERE activo = 1;

-- Optimizar ANALYZE para que SQLite tenga mejores estadisticas
ANALYZE;
"""


# ============================================================
# MIGRACION v6 — Permitir eliminacion de mesas
#   * Remueve la FK constraint entre ventas.mesa_id y mesas.id
#   * Permite crear/eliminar mesas sin restriccion de historial
#   * Las ventas conservan la referencia a mesa_id (puede ser NULL o referencia inexistente)
# ============================================================
MIGRACION_V6_SQL = """
-- Paso 1: Deshabilitar FK temporalmente
PRAGMA foreign_keys = OFF;

-- Paso 2: Remover columna venta_activa_id de mesas (causa FK circular)
CREATE TABLE IF NOT EXISTS mesas_new (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL UNIQUE,
    estado          TEXT    NOT NULL DEFAULT 'DISPONIBLE'
                            CHECK(estado IN ('DISPONIBLE','OCUPADA')),
    tipo            TEXT    NOT NULL DEFAULT 'MESA'
                            CHECK(tipo IN ('MESA','DOMICILIO'))
);

INSERT OR IGNORE INTO mesas_new (id, nombre, estado, tipo)
SELECT id, nombre, estado, COALESCE(tipo, 'MESA') FROM mesas;

DROP TABLE IF EXISTS mesas;
ALTER TABLE mesas_new RENAME TO mesas;

-- Paso 3: Remover FK constraint de ventas.mesa_id (recrear tabla sin la FK)
-- Primero eliminar triggers que referencian ventas
DROP TRIGGER IF EXISTS trg_venta_cerrar_validar;
DROP TRIGGER IF EXISTS trg_ventas_no_eliminar;
DROP TRIGGER IF EXISTS trg_ventas_cerrada_congelada;
DROP TRIGGER IF EXISTS trg_detalle_no_agregar_cerrada;
DROP TRIGGER IF EXISTS trg_detalle_no_modificar_cerrada;
DROP TRIGGER IF EXISTS trg_detalle_no_eliminar_cerrada;

CREATE TABLE IF NOT EXISTS ventas_new (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    consecutivo         INTEGER NOT NULL UNIQUE,
    mesa_id             INTEGER,
    usuario_id          INTEGER NOT NULL REFERENCES usuarios(id),
    caja_id             INTEGER REFERENCES cajas(id),
    fecha_hora          TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    subtotal            REAL    NOT NULL DEFAULT 0,
    descuento           REAL    NOT NULL DEFAULT 0,
    total               REAL    NOT NULL DEFAULT 0,
    metodo_pago         TEXT    CHECK(metodo_pago IN ('EFECTIVO','TRANSFERENCIA',NULL)),
    estado              TEXT    NOT NULL DEFAULT 'ABIERTA'
                                CHECK(estado IN ('ABIERTA','CERRADA','ANULADA')),
    cobro_procesado     INTEGER NOT NULL DEFAULT 0,
    cliente             TEXT,
    direccion_entrega   TEXT
);

INSERT OR IGNORE INTO ventas_new 
SELECT id, consecutivo, mesa_id, usuario_id, caja_id, fecha_hora, 
       subtotal, descuento, total, metodo_pago, estado, cobro_procesado,
       cliente, direccion_entrega FROM ventas;

DROP TABLE IF EXISTS ventas;
ALTER TABLE ventas_new RENAME TO ventas;

-- Paso 4: Recrear indices
CREATE INDEX IF NOT EXISTS idx_ventas_fecha     ON ventas(fecha_hora);
CREATE INDEX IF NOT EXISTS idx_ventas_estado    ON ventas(estado);
CREATE INDEX IF NOT EXISTS idx_ventas_caja      ON ventas(caja_id);
CREATE INDEX IF NOT EXISTS idx_ventas_metodo_pago ON ventas(metodo_pago);
CREATE INDEX IF NOT EXISTS idx_ventas_usuario     ON ventas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_ventas_mesa        ON ventas(mesa_id);
CREATE INDEX IF NOT EXISTS idx_ventas_consec      ON ventas(consecutivo);
CREATE INDEX IF NOT EXISTS idx_mesas_estado ON mesas(estado);
CREATE INDEX IF NOT EXISTS idx_mesas_tipo ON mesas(tipo);

-- Paso 5: Recrear triggers de protección del historial
CREATE TRIGGER IF NOT EXISTS trg_venta_cerrar_validar
BEFORE UPDATE ON ventas
FOR EACH ROW
WHEN NEW.estado = 'CERRADA' AND OLD.estado = 'ABIERTA'
BEGIN
    SELECT CASE
        WHEN (SELECT COUNT(*) FROM detalle_ventas WHERE venta_id = NEW.id) = 0
        THEN RAISE(ABORT, 'No se puede cerrar una venta sin productos.')
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_ventas_no_eliminar
BEFORE DELETE ON ventas
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: las ventas no se pueden eliminar, se deben anular.');
END;

CREATE TRIGGER IF NOT EXISTS trg_ventas_cerrada_congelada
BEFORE UPDATE ON ventas
FOR EACH ROW
WHEN OLD.estado IN ('CERRADA', 'ANULADA')
 AND (   NEW.consecutivo      !=  OLD.consecutivo
      OR NEW.mesa_id          IS NOT OLD.mesa_id
      OR NEW.usuario_id       !=  OLD.usuario_id
      OR NEW.caja_id          IS NOT OLD.caja_id
      OR NEW.fecha_hora       !=  OLD.fecha_hora
      OR NEW.subtotal         !=  OLD.subtotal
      OR NEW.descuento        !=  OLD.descuento
      OR NEW.total            !=  OLD.total
      OR NEW.metodo_pago      IS NOT OLD.metodo_pago
      OR NEW.cobro_procesado  !=  OLD.cobro_procesado )
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: una venta cerrada no se puede alterar.');
END;

CREATE TRIGGER IF NOT EXISTS trg_detalle_no_agregar_cerrada
BEFORE INSERT ON detalle_ventas
FOR EACH ROW
WHEN (SELECT estado FROM ventas WHERE id = NEW.venta_id) != 'ABIERTA'
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: no se pueden agregar productos a una venta cerrada.');
END;

CREATE TRIGGER IF NOT EXISTS trg_detalle_no_modificar_cerrada
BEFORE UPDATE ON detalle_ventas
FOR EACH ROW
WHEN (SELECT estado FROM ventas WHERE id = OLD.venta_id) != 'ABIERTA'
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: el detalle de una venta cerrada no se puede modificar.');
END;

CREATE TRIGGER IF NOT EXISTS trg_detalle_no_eliminar_cerrada
BEFORE DELETE ON detalle_ventas
FOR EACH ROW
WHEN (SELECT estado FROM ventas WHERE id = OLD.venta_id) != 'ABIERTA'
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: el detalle de una venta cerrada no se puede eliminar.');
END;

-- Paso 6: Re-habilitar FK
PRAGMA foreign_keys = ON;
"""


# ============================================================
# MIGRACION v7 — Agregar rol TECNICO a la tabla usuarios
#   * SQLite no permite ALTER TABLE para modificar CHECK constraints
#   * Si la tabla ya existe con el constraint correcto (desde SCHEMA_SQL), es NO-OP
#   * Si existe con constraint viejo, recrea la tabla
# ============================================================
MIGRACION_V7_SQL = """
-- Intentar recrear la tabla con el constraint correcto
-- Si ya existe con constraint viejo, esto lo arregla
-- Si ya existe con constraint nuevo, esto es NO-OP (ya tiene la restricción correcta)

-- Solo ejecutar si la tabla vieja tiene constraint incorrecto
-- Crear tabla temporal con constraint correcto
CREATE TABLE IF NOT EXISTS usuarios_new (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL,
    usuario         TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    rol             TEXT    NOT NULL CHECK(rol IN ('ADMIN','CAJERO','TECNICO')),
    activo          INTEGER NOT NULL DEFAULT 1,
    fecha_creacion  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Solo si usuarios_new está vacía, copiar datos de usuarios vieja
INSERT OR IGNORE INTO usuarios_new SELECT * FROM usuarios;

-- Cambiar tabla vieja por la nueva
DROP TABLE IF EXISTS usuarios;
ALTER TABLE usuarios_new RENAME TO usuarios;
"""


# ============================================================
# MIGRACION v8 — Agregar soporte para pagos MIXTO (efectivo + transferencia)
#   * Agregar columnas efectivo_pago y transferencia_pago a ventas
#   * Permitir MIXTO como valor de metodo_pago
#   * Esto permite registrar correctamente cuando un cliente paga con 2 métodos
# ============================================================
MIGRACION_V8_SQL = """
-- Paso 0: Deshabilitar FK y borrar triggers que hacen referencia a ventas
PRAGMA foreign_keys = OFF;
DROP TRIGGER IF EXISTS trg_ventas_no_eliminar;
DROP TRIGGER IF EXISTS trg_ventas_cerrada_congelada;
DROP TRIGGER IF EXISTS trg_detalle_no_agregar_cerrada;
DROP TRIGGER IF EXISTS trg_detalle_no_modificar_cerrada;
DROP TRIGGER IF EXISTS trg_detalle_no_eliminar_cerrada;

-- Paso 1: Crear tabla nueva con las columnas nuevas
CREATE TABLE IF NOT EXISTS ventas_new (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    consecutivo         INTEGER NOT NULL UNIQUE,
    mesa_id             INTEGER,
    usuario_id          INTEGER NOT NULL REFERENCES usuarios(id),
    caja_id             INTEGER REFERENCES cajas(id),
    fecha_hora          TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    subtotal            REAL    NOT NULL DEFAULT 0,
    descuento           REAL    NOT NULL DEFAULT 0,
    total               REAL    NOT NULL DEFAULT 0,
    metodo_pago         TEXT    CHECK(metodo_pago IN ('EFECTIVO','TRANSFERENCIA','MIXTO',NULL)),
    efectivo_pago       REAL    DEFAULT 0,
    transferencia_pago  REAL    DEFAULT 0,
    estado              TEXT    NOT NULL DEFAULT 'ABIERTA'
                                CHECK(estado IN ('ABIERTA','CERRADA','ANULADA')),
    cobro_procesado     INTEGER NOT NULL DEFAULT 0,
    cliente             TEXT,
    direccion_entrega   TEXT
);

-- Paso 2: Copiar datos de la tabla vieja a la nueva
INSERT INTO ventas_new 
    (id, consecutivo, mesa_id, usuario_id, caja_id, fecha_hora, subtotal, descuento, total,
     metodo_pago, efectivo_pago, transferencia_pago, estado, cobro_procesado, cliente, direccion_entrega)
SELECT 
    id, consecutivo, mesa_id, usuario_id, caja_id, fecha_hora, subtotal, descuento, total,
    metodo_pago, 
    CASE WHEN metodo_pago = 'EFECTIVO' THEN total ELSE 0 END,
    CASE WHEN metodo_pago = 'TRANSFERENCIA' THEN total ELSE 0 END,
    estado, cobro_procesado, cliente, direccion_entrega
FROM ventas;

-- Paso 3: Recrear indices
CREATE INDEX IF NOT EXISTS idx_ventas_fecha     ON ventas_new(fecha_hora);
CREATE INDEX IF NOT EXISTS idx_ventas_estado    ON ventas_new(estado);
CREATE INDEX IF NOT EXISTS idx_ventas_caja      ON ventas_new(caja_id);
CREATE INDEX IF NOT EXISTS idx_ventas_metodo_pago ON ventas_new(metodo_pago);
CREATE INDEX IF NOT EXISTS idx_ventas_usuario   ON ventas_new(usuario_id);
CREATE INDEX IF NOT EXISTS idx_ventas_mesa      ON ventas_new(mesa_id);
CREATE INDEX IF NOT EXISTS idx_ventas_consec    ON ventas_new(consecutivo);

-- Paso 4: Eliminar tabla vieja
DROP TABLE ventas;

-- Paso 5: Renombrar tabla nueva
ALTER TABLE ventas_new RENAME TO ventas;

-- Paso 6: Recrear los triggers
CREATE TRIGGER trg_ventas_no_eliminar
BEFORE DELETE ON ventas
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: las ventas no se pueden eliminar, se deben anular.');
END;

CREATE TRIGGER trg_ventas_cerrada_congelada
BEFORE UPDATE ON ventas
FOR EACH ROW
WHEN OLD.estado IN ('CERRADA', 'ANULADA')
 AND (   NEW.consecutivo      !=  OLD.consecutivo
      OR NEW.mesa_id          IS NOT OLD.mesa_id
      OR NEW.usuario_id       !=  OLD.usuario_id
      OR NEW.caja_id          IS NOT OLD.caja_id
      OR NEW.fecha_hora       !=  OLD.fecha_hora
      OR NEW.subtotal         !=  OLD.subtotal
      OR NEW.descuento        !=  OLD.descuento
      OR NEW.total            !=  OLD.total
      OR NEW.metodo_pago      IS NOT OLD.metodo_pago
      OR NEW.cobro_procesado  !=  OLD.cobro_procesado )
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: una venta cerrada no se puede alterar.');
END;

CREATE TRIGGER trg_detalle_no_agregar_cerrada
BEFORE INSERT ON detalle_ventas
FOR EACH ROW
WHEN (SELECT estado FROM ventas WHERE id = NEW.venta_id) != 'ABIERTA'
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: no se pueden agregar productos a una venta cerrada.');
END;

CREATE TRIGGER trg_detalle_no_modificar_cerrada
BEFORE UPDATE ON detalle_ventas
FOR EACH ROW
WHEN (SELECT estado FROM ventas WHERE id = OLD.venta_id) != 'ABIERTA'
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: el detalle de una venta cerrada no se puede modificar.');
END;

CREATE TRIGGER trg_detalle_no_eliminar_cerrada
BEFORE DELETE ON detalle_ventas
FOR EACH ROW
WHEN (SELECT estado FROM ventas WHERE id = OLD.venta_id) != 'ABIERTA'
BEGIN
    SELECT RAISE(ABORT,
        'Historial protegido: el detalle de una venta cerrada no se puede eliminar.');
END;

-- Paso 7: Reactivar FK
PRAGMA foreign_keys = ON;
"""


# Registro de migraciones: (version, descripcion, SQL)
# v1 es idempotente (CREATE IF NOT EXISTS) para compatibilidad con BD antiguas.
MIGRACIONES = [
    (1, "Esquema inicial: usuarios, categorias, productos, mesas, "
        "ventas, detalle_ventas, cajas, configuracion, indices y triggers base",
     SCHEMA_SQL),
    (2, "Integridad del negocio: historial protegido (ventas no se eliminan "
        "ni se alteran cuando estan cerradas) y una sola caja abierta",
     MIGRACION_V2_SQL),
    (3, "Retirar el NIT de la configuracion (restaurante local)",
     MIGRACION_V3_SQL),
    (4, "Mesas de domicilio (tipo, cliente y direccion de entrega)",
     MIGRACION_V4_SQL),
    (5, "Optimizacion para bajo consumo: indices compuestos y ANALYZE",
     MIGRACION_V5_SQL),
    (6, "Permitir eliminacion de mesas: remover FK constraint entre ventas.mesa_id y mesas.id",
     MIGRACION_V6_SQL),
    (7, "Agregar rol TECNICO a usuarios (CRMTECH - administración del sistema)",
     MIGRACION_V7_SQL),
    (8, "Pagos mixtos: agregar columnas efectivo_pago y transferencia_pago para manejar correctamente",
     MIGRACION_V8_SQL),
]


CONFIGURACION_DEFAULTS = {
    "nombre_negocio":       "Mi Negocio de Comidas",
    "direccion":            "",
    "telefono":             "",
    "logo_path":            "",
    "mensaje_final":        "¡Gracias por su visita!",
    "impresora":            "",
    "ancho_ticket_mm":      "80",
    "consecutivo_actual":   "0",
}


def inicializar_base_de_datos(db: DatabaseConnection):
    """
    Aplica todas las migraciones pendientes (versionadas en migraciones_bd),
    carga valores por defecto de configuracion y crea el ADMIN por defecto.
    Seguro para llamar cada vez que arranca la app: las migraciones ya
    aplicadas se omiten y las pendientes son incrementales, por lo que los
    datos existentes nunca se pierden.
    """
    conn = db.connection
    instalada = version_actual(db)

    for numero, descripcion, sql in MIGRACIONES:
        if numero <= instalada:
            continue
        _aplicar_migracion(conn, numero, descripcion, sql)

    # Insertar configuracion por defecto solo si no existen las claves
    for clave, valor in CONFIGURACION_DEFAULTS.items():
        conn.execute(
            "INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?);",
            (clave, valor),
        )
    conn.commit()

    # Crear usuario ADMIN por defecto si no hay ninguno
    _crear_admin_defecto(db)


def version_actual(db: DatabaseConnection) -> int:
    """Version de esquema instalada en la base de datos (0 si esta vacia)."""
    existe = db.fetchone(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='migraciones_bd';"
    )
    if not existe:
        return 0
    fila = db.fetchone("SELECT MAX(version) AS v FROM migraciones_bd;")
    return (fila["v"] or 0) if fila else 0


def _aplicar_migracion(conn, numero: int, descripcion: str, sql: str):
    """Aplica una migracion y registra su version. Solo se llama si esta pendiente."""
    print(f"  [BD] Aplicando migracion v{numero}: {descripcion}")
    try:
        conn.executescript(sql)
        conn.execute(
            "INSERT OR REPLACE INTO migraciones_bd (version, descripcion) "
            "VALUES (?, ?);",
            (numero, descripcion),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def verificar_base_de_datos(db: DatabaseConnection) -> dict:
    """
    Diagnostico de salud de la base de datos (para Puntos 11 y 12):
    - integridad: resultado de PRAGMA integrity_check ('ok' si esta sana)
    - claves_foraneas: cantidad de violaciones de FK
    - version: version de esquema instalada
    """
    reporte = {
        "integridad": db.integrity_check(),
        "claves_foraneas": len(db.foreign_key_check()),
        "version": version_actual(db),
    }
    reporte["ok"] = (
        reporte["integridad"] == "ok"
        and reporte["claves_foraneas"] == 0
    )
    return reporte


def _crear_admin_defecto(db: DatabaseConnection):
    """
    Si no existe ningun usuario ADMIN, crea uno con credenciales por defecto.
    Las credenciales se muestran en consola SOLO la primera vez.
    """
    existe = db.fetchone(
        "SELECT id FROM usuarios WHERE rol = 'ADMIN' AND activo = 1 LIMIT 1;"
    )
    if existe:
        return

    import bcrypt
    password_defecto = "admin123"
    hash_pwd = bcrypt.hashpw(password_defecto.encode(), bcrypt.gensalt()).decode()

    db.execute(
        """INSERT INTO usuarios (nombre, usuario, password_hash, rol, activo)
           VALUES (?, ?, ?, 'ADMIN', 1);""",
        ("Administrador", "admin", hash_pwd),
    )
    db.commit()
    print("=" * 50)
    print("  USUARIO ADMIN CREADO POR DEFECTO")
    print("  Usuario:    admin")
    print("  Contrasena: admin123")
    print("  Cambiela despues de iniciar sesion.")
    print("=" * 50)

