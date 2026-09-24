# 📚 DOCUMENTACIÓN COMPLETA — CRM POS

> Guía técnica y estructura del proyecto POS para comidas rápidas.

---

## 📋 TABLA DE CONTENIDOS

1. [Visión General](#visión-general)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Tecnologías Utilizadas](#tecnologías-utilizadas)
4. [Base de Datos](#base-de-datos)
5. [Módulos y Servicios](#módulos-y-servicios)
6. [Flujos de Funcionamiento](#flujos-de-funcionamiento)
7. [Datos Sensibles y Seguridad](#datos-sensibles-y-seguridad)
8. [Configuración y Deployment](#configuración-y-deployment)
9. [API de Servicios](#api-de-servicios)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 VISIÓN GENERAL

### ¿Qué es?
Sistema POS (Point of Sale) diseñado específicamente para negocios de comidas rápidas. 
Funciona **100% local** sin depender de internet.

### Características Principales
- ✅ Gestión de mesas y pedidos
- ✅ Sistema de caja (apertura/cierre)
- ✅ Impresión en impresora térmica
- ✅ Reportes y exportación a Excel
- ✅ Control de usuarios con permisos (ADMIN/CAJERO)
- ✅ Histórico completo de ventas
- ✅ Optimizado para bajo-resource (2GB RAM mínimo)
- ✅ Actualizaciones automáticas desde GitHub

### Requerimientos Mínimos
- Windows 7+
- 2GB RAM
- Procesador dual-core 2GHz+
- SQLite (incluido)
- Impresora térmica (58mm o 80mm) — opcional

---

## 📁 ESTRUCTURA DEL PROYECTO

```
CRM/
│
├── main.py                          # Punto de entrada principal
├── requirements.txt                 # Dependencias Python
├── versioninfo.json                 # Información de versión (para updates)
│
├── app/                             # Carpeta principal de la app
│   │
│   ├── __init__.py
│   │
│   ├── database/                    # Capa de datos
│   │   ├── connection.py            # Conexión SQLite
│   │   ├── migrations.py            # Esquema y migraciones
│   │   ├── seeder.py                # Datos iniciales
│   │   └── __init__.py
│   │
│   ├── models/                      # Modelos de datos
│   │   ├── usuario.py               # Usuario (ADMIN/CAJERO)
│   │   ├── producto.py              # Productos del menú
│   │   ├── mesa.py                  # Mesas del local
│   │   ├── venta.py                 # Ventas/facturas
│   │   ├── caja.py                  # Control de caja
│   │   └── __init__.py
│   │
│   ├── services/                    # Lógica de negocio
│   │   ├── auth_service.py          # Autenticación y permisos
│   │   ├── usuario_service.py       # Gestión de usuarios
│   │   ├── producto_service.py      # Gestión de productos
│   │   ├── mesa_service.py          # Gestión de mesas
│   │   ├── pedido_service.py        # Gestión de pedidos
│   │   ├── caja_service.py          # Gestión de caja
│   │   ├── venta_service.py         # Gestión de ventas
│   │   ├── reporte_service.py       # Reportes
│   │   ├── comprobante_service.py   # Generación de comprobantes
│   │   ├── backup_service.py        # Backups de BD
│   │   ├── configuracion_service.py # Configuración del negocio
│   │   ├── cobro_service.py         # Lógica de cobro
│   │   ├── permisos.py              # Definición de permisos
│   │   └── __init__.py
│   │
│   ├── ui/                          # Interfaz gráfica (PySide6)
│   │   ├── login_window.py          # Ventana de login
│   │   ├── main_window.py           # Ventana principal
│   │   ├── themes/                  # Sistema de colores
│   │   │   ├── colors.py            # Paleta centralizada
│   │   │   └── __init__.py
│   │   │
│   │   ├── screens/                 # Pantallas (Puntos 2-11)
│   │   │   ├── _base_screen.py      # Clase base para screens
│   │   │   ├── productos_screen.py  # Gestión de productos (P2/3)
│   │   │   ├── mesas_screen.py      # Tablero de mesas (P4)
│   │   │   ├── pedido_screen.py     # Pantalla de pedido (P4)
│   │   │   ├── cobro_screen.py      # Pantalla de cobro (P5)
│   │   │   ├── caja_screen.py       # Gestión de caja (P9)
│   │   │   ├── historial_screen.py  # Historial de ventas (P7)
│   │   │   ├── reportes_screen.py   # Reportes y Excel (P8)
│   │   │   ├── usuarios_screen.py   # Gestión de usuarios (P3)
│   │   │   ├── configuracion_screen.py # Configuración (P10)
│   │   │   └── __init__.py
│   │   │
│   │   ├── widgets/                 # Componentes reutilizables
│   │   │   ├── catalogo_widget.py   # Catálogo de productos
│   │   │   ├── mesa_card.py         # Tarjeta visual de mesa
│   │   │   ├── producto_item.py     # Item de producto
│   │   │   ├── dialogo_usuario.py   # Diálogo crear/editar usuario
│   │   │   ├── dialogo_password.py  # Diálogo cambiar contraseña
│   │   │   ├── dialogo_domicilio.py # Diálogo de entrega
│   │   │   └── __init__.py
│   │   │
│   │   └── __init__.py
│   │
│   ├── printing/                    # Impresión térmica
│   │   ├── escpos.py                # Protocolo ESCPOS
│   │   ├── printer_manager.py       # Gestor de impresoras
│   │   ├── ticket_formatter.py      # Formato de ticket
│   │   └── __init__.py
│   │
│   ├── utils/                       # Utilidades
│   │   ├── helpers.py               # Funciones auxiliares
│   │   ├── validators.py            # Validadores de entrada
│   │   ├── logger.py                # Sistema de logging
│   │   ├── paths.py                 # Rutas del sistema
│   │   ├── cache.py                 # Caché de datos
│   │   ├── debounce.py              # Debouncer para UI
│   │   ├── updater.py               # Sistema de actualizaciones
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── comprobantes/                    # Facturas/comprobantes (.txt)
│   └── .gitkeep
│
├── reportes/                        # Reportes exportados (.xlsx)
│   └── .gitkeep
│
├── backups/                         # Copias de seguridad de BD
│   └── .gitkeep
│
└── .gitignore                       # Archivos a ignorar en git

```

---

## 🛠️ TECNOLOGÍAS UTILIZADAS

### Backend
| Tecnología | Versión | Uso |
|------------|---------|-----|
| **Python** | 3.12+ | Lenguaje principal |
| **SQLite** | 3.x | Base de datos local |
| **requests** | 2.31+ | Descargas de actualizaciones |

### Frontend
| Tecnología | Versión | Uso |
|------------|---------|-----|
| **PySide6** | 6.x | Interfaz gráfica |
| **ReportLab** | 4.x | Generación de comprobantes |
| **openpyxl** | 3.x | Exportación a Excel |

### DevOps
| Herramienta | Uso |
|-------------|-----|
| **Git** | Control de versiones |
| **GitHub** | Repositorio y releases |
| **PyInstaller** | Empaquetamiento a .exe |

---

## 🗄️ BASE DE DATOS

### Esquema SQLite

#### Tabla: usuarios
```sql
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol TEXT CHECK(rol IN ('ADMIN', 'CAJERO')) NOT NULL,
    estado TEXT DEFAULT 'Activo',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Índices**:
- `idx_usuarios_estado`: Búsqueda por estado

#### Tabla: productos
```sql
CREATE TABLE productos (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    categoria_id INTEGER NOT NULL,
    precio REAL NOT NULL,
    descripcion TEXT,
    estado TEXT DEFAULT 'Activo',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion DATETIME,
    FOREIGN KEY(categoria_id) REFERENCES categorias(id)
);
```

#### Tabla: mesas
```sql
CREATE TABLE mesas (
    id INTEGER PRIMARY KEY,
    numero INTEGER NOT NULL,
    nombre TEXT UNIQUE NOT NULL,
    estado TEXT DEFAULT 'DISPONIBLE',
    tipo TEXT DEFAULT 'PRESENCIAL',
    venta_activa_id INTEGER,
    FOREIGN KEY(venta_activa_id) REFERENCES ventas(id)
);
```

**Estados**: `DISPONIBLE`, `OCUPADA`  
**Tipos**: `PRESENCIAL`, `DOMICILIO`

#### Tabla: ventas
```sql
CREATE TABLE ventas (
    id INTEGER PRIMARY KEY,
    consecutivo TEXT UNIQUE NOT NULL,
    mesa_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    fecha_venta DATETIME DEFAULT CURRENT_TIMESTAMP,
    subtotal REAL,
    descuento REAL DEFAULT 0,
    total REAL NOT NULL,
    metodo_pago TEXT CHECK(metodo_pago IN ('EFECTIVO', 'TRANSFERENCIA')),
    estado TEXT DEFAULT 'Abierta',
    cliente TEXT,
    direccion TEXT,
    FOREIGN KEY(mesa_id) REFERENCES mesas(id),
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
);
```

**Métodos de pago**: `EFECTIVO`, `TRANSFERENCIA`  
**Estados**: `Abierta`, `Cerrada`, `Anulada`

#### Tabla: detalles_venta
```sql
CREATE TABLE detalles_venta (
    id INTEGER PRIMARY KEY,
    venta_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad REAL NOT NULL,
    precio_unitario REAL NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY(venta_id) REFERENCES ventas(id),
    FOREIGN KEY(producto_id) REFERENCES productos(id)
);
```

#### Tabla: caja
```sql
CREATE TABLE caja (
    id INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATETIME,
    monto_inicial REAL NOT NULL,
    total_efectivo REAL DEFAULT 0,
    total_transferencia REAL DEFAULT 0,
    efectivo_esperado REAL,
    efectivo_contado REAL,
    diferencia REAL,
    observaciones TEXT,
    estado TEXT DEFAULT 'Abierta',
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
);
```

**Estados**: `Abierta`, `Cerrada`

### Migraciones
Las migraciones se ejecutan automáticamente al iniciar. Ver `app/database/migrations.py`.

**Versión actual**: v5 (con índices optimizados)

---

## 🔧 MÓDULOS Y SERVICIOS

### AuthService (app/services/auth_service.py)

```python
auth = AuthService(db)

# Login
usuario = auth.login("admin", "password123")  # Retorna dict con datos

# Verificar permisos
puede = auth.puede("VER_REPORTES")  # True/False

# Cambiar contraseña
auth.cambiar_password_actual("pass_viejo", "pass_nuevo")

# Verificar si está autenticado
usuario_actual = auth.usuario_actual()  # dict o None
```

**Permisos disponibles**:
- `ABRIR_CERRAR_CAJA`
- `VER_REPORTES`
- `CREAR_USUARIO`
- `EDITAR_PRODUCTOS`
- etc.

### ProductoService

```python
ps = ProductoService(db, auth)

# Listar productos (con caché)
productos = ps.listar()  # TTL 300s

# Crear producto
ps.crear("Hamburguesa", 1, 12.50, "Hamburguesa sencilla")

# Actualizar producto
ps.actualizar(1, {"precio": 13.00})

# Desactivar producto
ps.desactivar(1)
```

### PedidoService

```python
ped = PedidoService(db, auth)

# Abrir mesa / crear venta
venta_id = ped.abrir_mesa(mesa_id)

# Agregar producto al pedido
ped.agregar_producto(venta_id, producto_id, cantidad=2)

# Ver detalles
detalles = ped.detalles_pedido(venta_id)

# Modificar cantidad
ped.modificar_cantidad(venta_id, detalle_id, nueva_cantidad=3)

# Quitar producto
ped.quitar_producto(venta_id, detalle_id)

# Resumen del pedido
resumen = ped.resumen_pedido(venta_id)  # total, detalles, etc

# Cerrar venta (cobro)
ped.cerrar_pedido(venta_id, metodo_pago, monto_recibido)
```

### ReporteService

```python
repo = ReporteService(db, auth)

# Resumen general
resumen = repo.resumen_ventas("2026-01-01", "2026-09-19")

# Productos vendidos
productos = repo.productos_vendidos(desde, hasta)

# Ventas por cajero
cajeros = repo.ventas_por_cajero(desde, hasta)

# Ventas por mesa
mesas = repo.ventas_por_mesa(desde, hasta)

# Exportar a Excel
repo.exportar_excel(desde, hasta, ruta_archivo)
```

### CajaService

```python
caja = CajaService(db, auth)

# Abrir caja
caja.abrir(usuario_id, monto_inicial=200000)

# Caja abierta actual
caja_actual = caja.caja_abierta()  # dict o None

# Actualizar totales
caja.actualizar_totales(caja_id)

# Cerrar caja
caja.cerrar(caja_id, efectivo_contado, observaciones)

# Historial
cierres = caja.historial()  # Último mes
```

---

## 🔄 FLUJOS DE FUNCIONAMIENTO

### 1. Flujo de Login

```
usuario ingresa credenciales
    ↓
auth_service.login(usuario, password)
    ↓
Se valida contra BD (password hasheado)
    ↓
Si correcto → se establece sesión
    ↓
Si incorrecto → error "Usuario o contraseña inválidos"
    ↓
Se abre MainWindow
```

### 2. Flujo de Pedido

```
1. Usuario selecciona mesa DISPONIBLE
    ↓
2. pedido_service.abrir_mesa(mesa_id)
    ↓ Crea venta (estado: "Abierta")
    ↓
3. Usuario agrega productos
    ↓ pedido_service.agregar_producto()
    ↓ Se guarda cada línea en detalles_venta
    ↓
4. Usuario modifica cantidades
    ↓ pedido_service.modificar_cantidad()
    ↓
5. Usuario cobra
    ↓ Selecciona: EFECTIVO o TRANSFERENCIA
    ↓
6. pedido_service.cerrar_pedido()
    ↓ Venta cambia a estado "Cerrada"
    ↓ Mesa vuelve a DISPONIBLE
    ↓
7. Se genera comprobante e imprime
    ↓
8. Se actualiza caja
    ↓
Listo
```

### 3. Flujo de Caja

```
MAÑANA:
1. Admin abre caja
    ↓ caja.abrir(usuario_id, 200000)
    ↓ estado = "Abierta"
    
DURANTE EL DÍA:
2. Se realizan ventas en efectivo
    ↓ caja_service.actualizar_totales()
    ↓ suma automaticamente el efectivo de ventas

CIERRE:
3. Admin cierra caja
    ↓ Ingresa efectivo físico contado
    ↓ caja.cerrar(caja_id, efectivo_contado)
    ↓
4. Sistema calcula diferencia
    ↓ esperado = 200000 + total_ventas_efectivo
    ↓ diferencia = esperado - contado
    ↓ Si diferencia > 0 → "FALTANTE"
    ↓ Si diferencia < 0 → "SOBRANTE"
    ↓ Si diferencia = 0 → "CUADRA"
```

### 4. Flujo de Actualización

```
Usuario abre la app
    ↓
main.py carga
    ↓
check_and_update_with_dialog()
    ↓
updater.check_updates()
    ↓ Conecta a GitHub y lee versioninfo.json
    ↓ Compara versiones
    
Si versión Nueva > Actual:
    ↓ Muestra diálogo "¿Actualizar?"
    ↓
Si usuario dice "SÍ":
    ↓ updater.download_update(url)
    ↓ Descarga nuevo .exe
    ↓ updater.install_update()
    ↓ Script batch reemplaza .exe
    ↓ Se reinicia app automáticamente
    ↓ Abre con versión nueva
    
Si usuario dice "NO" o sin conexión:
    ↓ Continúa con versión actual
```

---

## 🔒 DATOS SENSIBLES Y SEGURIDAD

### Datos Sensibles

| Dato | Dónde se guarda | Encriptación | Acceso |
|------|-----------------|-------------|--------|
| **Contraseñas** | BD (usuarios) | SHA256 | Solo auth_service |
| **Ventas** | BD (ventas, detalles) | Texto plano | Servicios + UI |
| **Comprobantes** | Archivos .txt | Texto plano | Cliente puede leer |
| **Configuración** | BD + archivos | Texto plano | Admin solo |
| **Logs** | Archivos .log | Texto plano | Sistema |

### Medidas de Seguridad Implementadas

✅ **Contraseñas hasheadas** (SHA256)
```python
import hashlib
password_hash = hashlib.sha256(password.encode()).hexdigest()
```

✅ **Permisos por rol**
```python
if not auth.puede("EDITAR_PRODUCTOS"):
    raise PermissionError("No tiene permiso")
```

✅ **Validación de entrada**
```python
from app.utils.validators import validar_usuario, validar_password
valido, msg = validar_usuario("juan")  # True or False
```

✅ **Transacciones SQLite**
```python
try:
    db.execute("INSERT INTO ventas...")
    db.commit()  # Confirmado
except:
    db.rollback()  # Deshacer si hay error
```

✅ **Gestión de sesiones**
```python
# Sesión se cierra al hacer logout
auth.cerrar_sesion()
```

### Datos NO Sensibles (pero privados)

- Nombres de clientes
- Direcciones de entrega
- Historial de transacciones
- Información del negocio (nombre, dirección, etc.)

---

## ⚙️ CONFIGURACIÓN Y DEPLOYMENT

### Desarrollo

```bash
# Clonar repo
git clone https://github.com/TUUSUARIO/CRM.git
cd CRM

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python main.py
```

### Producción (Generar .exe)

```bash
# Instalar PyInstaller
pip install pyinstaller

# Generar .exe
pyinstaller --onefile \
  --windowed \
  --name "CRM" \
  --icon app/assets/icon.ico \
  main.py

# El .exe está en: dist/CRM.exe
```

### Distribución

1. **Primera instalación**:
   - Usuario descarga `CRM.exe` desde GitHub Releases
   - Ejecuta el archivo
   - Se crea BD en `%APPDATA%\CRM\`

2. **Actualizaciones**:
   - Usuario abre la app
   - App verifica updates automáticamente
   - Si hay update, pregunta
   - Si acepta, descarga e instala automáticamente

---

## 📡 API DE SERVICIOS

### AuthService

```python
auth.login(usuario: str, password: str) → dict
auth.logout() → None
auth.usuario_actual() → dict | None
auth.puede(permiso: str) → bool
auth.cambiar_password_actual(vieja: str, nueva: str) → bool
```

### ProductoService

```python
ps.listar() → list[dict]
ps.obtener(id: int) → dict
ps.crear(nombre, categoria_id, precio, desc) → int
ps.actualizar(id: int, datos: dict) → bool
ps.desactivar(id: int) → bool
ps.listar_categorias() → list[dict]
```

### PedidoService

```python
ped.abrir_mesa(mesa_id, cliente=None, direccion=None) → int (venta_id)
ped.agregar_producto(venta_id, producto_id, cantidad) → bool
ped.modificar_cantidad(venta_id, detalle_id, nueva_cant) → bool
ped.quitar_producto(venta_id, detalle_id) → bool
ped.detalles_pedido(venta_id) → list[dict]
ped.resumen_pedido(venta_id) → dict
ped.cerrar_pedido(venta_id, metodo_pago, monto_recibido) → dict
ped.cancelar_pedido(mesa_id) → bool
ped.listar_mesas() → list[dict]
ped.datos_mesa_activa(mesa_id) → dict
```

---

## 🐛 TROUBLESHOOTING

### "No se puede conectar a la base de datos"
**Causa**: Archivo .db corrupto o permisos incorrectos
**Solución**:
```bash
# Eliminar BD corrupta
rm %APPDATA%\CRM\pos.db

# Ejecutar app de nuevo
python main.py
# Se creará BD nueva con seeder
```

### "Error de autenticación"
**Causa**: Usuario/password incorrecto
**Solución**:
```python
# Usuario por defecto (después de seeder):
usuario: admin
password: admin123
```

### "La app no actualiza"
**Causa**: 
- Sin conexión a internet
- URL de GitHub incorrecto
- Repositorio es PRIVATE (debe ser PUBLIC)

**Solución**:
```python
# Editar app/updater.py
# Verificar VERSION_CHECK_URL
print(VERSION_CHECK_URL)  # Ver URL exacta
# Abrir URL en navegador, debe mostrar JSON
```

### "Impresora no imprime"
**Causa**: Driver no instalado o puerto incorrecto
**Solución**:
1. Ver Configuración → Impresoras
2. Seleccionar impresora correcta
3. Hacer test print
4. Si sigue sin funcionar, ver logs en `/logs/`

### "Errores de compilación al hacer .exe"
**Causa**: Falta algún módulo en requirements.txt
**Solución**:
```bash
pip install -r requirements.txt
pyinstaller --onefile --windowed main.py
```

---

## 📞 SOPORTE

Para problemas:
1. Ver logs en `logs/app.log`
2. Verificar error exacto
3. Buscar en este documento
4. Si persiste, contactar al desarrollador

---

## ✅ CHECKLIST DE FUNCIONALIDADES

- [x] Login con permisos
- [x] Gestión de usuarios
- [x] Gestión de productos
- [x] Tablero de mesas
- [x] Toma de pedidos
- [x] Sistema de cobro
- [x] Impresora térmica
- [x] Historial de ventas
- [x] Reportes y Excel
- [x] Apertura/cierre de caja
- [x] Backups automáticos
- [x] Configuración del negocio
- [x] Actualizaciones automáticas
- [x] Optimización para bajo-resource

---

**Documentación v2.0**  
**Última actualización**: Septiembre 19, 2026  
**Versión del proyecto**: 1.0 - Production Ready
