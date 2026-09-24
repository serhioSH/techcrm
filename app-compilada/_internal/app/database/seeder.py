# ============================================================
#  app/database/seeder.py
#  Datos iniciales para el negocio de comidas rapidas
#  Se ejecuta SOLO la primera vez (si no hay datos)
# ============================================================
from app.database.connection import DatabaseConnection


# ---------- Categorias iniciales ----------
CATEGORIAS = [
    "Hamburguesas",
    "Perros Calientes",
    "Papas y Snacks",
    "Bebidas",
    "Combos",
    "Postres",
]

# ---------- Productos iniciales ----------
# (nombre, descripcion, categoria_nombre, precio)
PRODUCTOS = [
    # Hamburguesas
    ("Hamburguesa Sencilla",   "Pan, carne, lechuga, tomate",             "Hamburguesas",      12000),
    ("Hamburguesa Doble",      "Doble carne, queso doble, salsas",        "Hamburguesas",      18000),
    ("Hamburguesa Especial",   "Carne, jamon, queso, huevo, salsas",      "Hamburguesas",      20000),
    ("Hamburguesa Pollo",      "Pechuga apanada, lechuga, tomate",        "Hamburguesas",      15000),
    ("Hamburguesa BBQ",        "Carne, tocineta, salsa BBQ, queso",       "Hamburguesas",      22000),
    # Perros Calientes
    ("Perro Sencillo",         "Salchicha, mostaza, ketchup",             "Perros Calientes",   8000),
    ("Perro Especial",         "Salchicha, queso, papitas, salsas",       "Perros Calientes",  12000),
    ("Perro Ranchero",         "Salchicha, tocineta, queso, pico gallo",  "Perros Calientes",  15000),
    # Papas y Snacks
    ("Papas Fritas Pequenas",  "Porcion pequena de papas fritas",         "Papas y Snacks",     5000),
    ("Papas Fritas Grandes",   "Porcion grande de papas fritas",          "Papas y Snacks",     8000),
    ("Papas con Queso",        "Papas fritas baneadas en queso",          "Papas y Snacks",    10000),
    ("Papas con Tocineta",     "Papas fritas, tocineta, queso",           "Papas y Snacks",    12000),
    ("Aros de Cebolla",        "Anillos de cebolla apanados",             "Papas y Snacks",     8000),
    # Bebidas
    ("Gaseosa Personal",       "Coca-Cola, Pepsi o similar 300ml",        "Bebidas",            3000),
    ("Gaseosa Grande",         "Gaseosa 600ml",                           "Bebidas",            5000),
    ("Agua Botella",           "Agua mineral 600ml",                      "Bebidas",            2500),
    ("Jugo Natural",           "Jugo de fruta natural del dia",           "Bebidas",            5000),
    ("Limonada Natural",       "Limonada fria natural",                   "Bebidas",            6000),
    ("Malteada",               "Malteada de chocolate, fresa o vainilla", "Bebidas",            9000),
    # Combos
    ("Combo Personal",         "Hamburguesa sencilla + papas + gaseosa",  "Combos",            18000),
    ("Combo Doble",            "Hamburguesa doble + papas grandes + gas", "Combos",            25000),
    ("Combo Perro",            "Perro especial + papas pequenas + gaseosa","Combos",            18000),
    # Postres
    ("Brownie",                "Brownie de chocolate casero",             "Postres",            5000),
    ("Helado 1 Bola",          "Helado de vainilla, chocolate o fresa",   "Postres",            4000),
]

# ---------- Mesas iniciales ----------
# (nombre, tipo) — tipo: MESA (salon) | DOMICILIO (entrega a casa)
MESAS = [
    ("Mesa 1", "MESA"),
    ("Mesa 2", "MESA"),
    ("Mesa 3", "MESA"),
    ("Mesa 4", "MESA"),
    ("Mesa 5", "MESA"),
    ("Mesa 6", "MESA"),
    ("Mesa 7", "MESA"),
    ("Mesa 8", "MESA"),
    ("Mesa 9", "MESA"),
    ("Mesa 10", "MESA"),
    ("Domicilio 1", "DOMICILIO"),
]


def ejecutar_seeder(db: DatabaseConnection) -> dict:
    """
    Inserta datos iniciales si aun no existen.
    Es idempotente: puede llamarse multiples veces sin duplicar datos.
    Retorna un dict con el conteo de registros insertados.
    """
    resultado = {"categorias": 0, "productos": 0, "mesas": 0, "usuarios": 0}

    # ---- Usuarios (admin = ADMIN, CRMTECH = TECNICO, cajero = CAJERO) ----
    usuarios_iniciales = [
        # Usuarios principales requeridos
        ("Admin - Dueño", "admin", "admin123", "ADMIN"),           # Dueño del negocio - ACCESO TOTAL
        ("CRMTECH Admin", "CRMTECH", "TECHPIXELC", "TECNICO"),     # Admin técnico - acceso limitado
        ("Cajero", "cajero", "cajero123", "CAJERO"),                # Usuario CAJERO
        # Usuario legado - AHORA ES TECNICO
        ("TechCRM Admin", "techcrm", "techpixelc", "TECNICO"),     # Técnico - GitHub config y reinicio BD
    ]
    from app.services.auth_service import AuthService
    auth = AuthService(db)
    for nombre, usuario, pwd, rol in usuarios_iniciales:
        existe = db.fetchone("SELECT id, rol FROM usuarios WHERE usuario=?;", (usuario,))
        if not existe:
            auth.registrar_usuario(nombre, usuario, pwd, rol)
            resultado["usuarios"] += 1
        else:
            # Si existe pero tiene rol o nombre diferente, ACTUALIZAR SIEMPRE
            if existe["rol"] != rol:
                try:
                    db.execute("UPDATE usuarios SET rol=? WHERE usuario=?;", (rol, usuario))
                    db.commit()
                except Exception:
                    # Si falla por CHECK constraint, ignorar (la migración V7 lo arreglará)
                    db.rollback()

    # ---- Categorias ----
    for nombre in CATEGORIAS:
        existe = db.fetchone("SELECT id FROM categorias WHERE nombre=?;", (nombre,))
        if not existe:
            db.execute("INSERT INTO categorias (nombre) VALUES (?);", (nombre,))
            resultado["categorias"] += 1
    db.commit()

    # ---- Productos ----
    for nombre, desc, cat_nombre, precio in PRODUCTOS:
        existe = db.fetchone("SELECT id FROM productos WHERE nombre=?;", (nombre,))
        if not existe:
            cat = db.fetchone("SELECT id FROM categorias WHERE nombre=?;", (cat_nombre,))
            cat_id = cat["id"] if cat else None
            db.execute(
                """INSERT INTO productos (nombre, descripcion, categoria_id, precio, activo)
                   VALUES (?, ?, ?, ?, 1);""",
                (nombre, desc, cat_id, precio),
            )
            resultado["productos"] += 1
    db.commit()

    # ---- Mesas ----
    for nombre, tipo in MESAS:
        existe = db.fetchone("SELECT id FROM mesas WHERE nombre=?;", (nombre,))
        if not existe:
            db.execute(
                "INSERT INTO mesas (nombre, estado, tipo) "
                "VALUES (?, 'DISPONIBLE', ?);",
                (nombre, tipo),
            )
            resultado["mesas"] += 1
    db.commit()

    # ---- Configuración de Logo (NUEVO) ----
    # Verificar si ya tiene logo configurado, si no, usar el logo.jpeg de data
    import os
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "logo.jpeg")
    if os.path.exists(logo_path):
        config_existe = db.fetchone("SELECT clave FROM configuracion WHERE clave='logo_path';")
        if not config_existe:
            db.execute(
                "INSERT INTO configuracion (clave, valor) VALUES (?, ?);",
                ("logo_path", logo_path)
            )
            db.commit()

    return resultado


def ya_fue_inicializado(db: DatabaseConnection) -> bool:
    """Verifica si el seeder ya fue ejecutado (si hay mesas o productos)."""
    row = db.fetchone("SELECT COUNT(*) AS n FROM mesas;")
    return (row["n"] if row else 0) > 0
