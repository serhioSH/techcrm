# 📋 DOCUMENTACIÓN DE ARCHIVOS - TECHCRM POS

**Guía completa de todos los archivos que se subirán a GitHub**

---

## 📑 Tabla de Contenidos

1. [Archivos Raíz](#archivos-raíz)
2. [Directorio `/app` - Código Principal](#directorio-app---código-principal)
3. [Archivos de Configuración](#archivos-de-configuración)
4. [Archivos de Construcción y Distribución](#archivos-de-construcción-y-distribución)
5. [Archivos Excluidos (NO se suben)](#archivos-excluidos-no-se-suben)
6. [Estructura Visual Completa](#estructura-visual-completa)

---

## 🔵 ARCHIVOS RAÍZ

### Archivos Críticos (SIEMPRE se suben)

#### `main.py` ⭐
- **Descripción**: Punto de entrada principal de la aplicación
- **Función**: 
  - Inicia el logger
  - Verifica actualizaciones automáticas
  - Conecta a la base de datos
  - Ejecuta seeder si es primera vez
  - Abre ventana de login
- **Tamaño**: ~2 KB
- **Dependencias**: PySide6, requests

#### `requirements.txt` ⭐
- **Descripción**: Dependencias de Python necesarias
- **Contenido**:
  - `PySide6==6.6.1` - Interfaz gráfica (Qt para Python)
  - `openpyxl==3.1.5` - Generación de reportes Excel
  - `requests==2.31.0` - HTTP requests para actualizaciones
  - `python-escpos==3.1` - Manejo de impresoras térmicas
  - `Pillow==10.1.0` - Procesamiento de imágenes
- **Uso**: `pip install -r requirements.txt`

#### `README.md` ⭐
- **Descripción**: Documentación general del proyecto
- **Contiene**:
  - Descripción general de la aplicación
  - Características principales
  - Guía de inicio rápido
  - Estructura del proyecto
  - Sistema de actualizaciones
  - Tabla de tecnologías usadas
  - Troubleshooting básico

#### `.gitignore` ⭐
- **Descripción**: Define qué archivos NO se suben a Git
- **Excluye**:
  - `__pycache__/` - Archivos compilados de Python
  - `*.pyc` - Bytecode compilado
  - `dist/`, `build/` - Artifacts de compilación
  - `data/*.db` - Base de datos local (datos reales)
  - `backups/` - Respaldos locales
  - `reportes/*.xlsx` - Reportes generados
  - `logs/*.log` - Archivos de log
  - `.env` - Variables de entorno sensibles
  - `.vscode/`, `.idea/` - Configuraciones de IDE

#### `version.json` ⭐
- **Descripción**: Información de versión para actualizaciones automáticas
- **Estructura**:
  ```json
  {
    "version": "1.0",
    "download_url": "https://github.com/USUARIO/REPO/releases/download/v1.0/CRM.exe",
    "release_date": "2026-09-23",
    "description": "Descripción del release"
  }
  ```
- **Actualizar**: Cada que hagas un release en GitHub

#### `DOCUMENTACION.md`
- **Descripción**: Documentación técnica completa del proyecto
- **Contiene**:
  - Estructura de directorios detallada
  - Descripción de cada módulo
  - Guía de desarrollo
  - Troubleshooting técnico

#### `GITHUB_SETUP.md`
- **Descripción**: Guía paso a paso para configurar actualizaciones en GitHub
- **Contiene**:
  - Configuración de repositorio
  - Cómo crear releases
  - Sistema de actualizaciones automáticas
  - Variables de entorno necesarias

#### `ACTUALIZACION.md`
- **Descripción**: Registro de cambios y actualizaciones realizadas
- **Contiene**:
  - Historial de cambios por versión
  - Notas de liberación

---

## 🟠 DIRECTORIO `/app` - CÓDIGO PRINCIPAL

### `/app/__init__.py`
- Archivo vacío que marca a `app` como paquete Python
- Permite `from app.xxx import yyy`

### `/app/main.py` (alternativo)
- Duplicado de `main.py` en algunos proyectos
- Generalmente NO está en la raíz

---

## 📂 `/app/database/` - Gestión de Base de Datos

#### `connection.py`
- **Descripción**: Conexión singleton a SQLite
- **Clases**: `DatabaseConnection`
- **Métodos principales**:
  - `_connect()` - Establece conexión
  - `connection` - Propiedad que retorna conexión
- **Ubicación BD**: `data/crm.db`

#### `migrations.py`
- **Descripción**: Gestión de esquema de base de datos
- **Funciones principales**:
  - `inicializar_base_de_datos()` - Crea tablas si no existen
  - `version_actual()` - Obtiene versión de BD
  - `_aplicar_migracion()` - Aplica cambios de esquema
  - `verificar_base_de_datos()` - Valida integridad
  - `_crear_admin_defecto()` - Usuario admin inicial
- **Tablas**: usuarios, productos, categorias, mesas, ventas, detalles_venta, caja

#### `seeder.py`
- **Descripción**: Datos iniciales para primera ejecución
- **Funciones principales**:
  - `ejecutar_seeder()` - Carga datos de prueba
  - `ya_fue_inicializado()` - Verifica si ya corrió
- **Datos iniciales**:
  - Usuarios: admin, cajero1
  - Categorías: Comidas, Bebidas, Postres
  - Productos: 20+ productos de ejemplo
  - Mesas: 10 mesas de ejemplo

#### `__init__.py`
- Marca a `database` como paquete

---

## 🎨 `/app/models/` - Modelos de Datos

#### `usuario.py`
- **Clase**: `Usuario`
- **Atributos**: id, nombre, usuario, password, rol, activo
- **Métodos**:
  - `es_admin()` - Verifica si es administrador
  - `es_cajero()` - Verifica si es cajero
  - `esta_activo()` - Verifica estado activo

#### `producto.py`
- **Clase**: `Producto`
- **Atributos**: id, nombre, descripcion, categoria, precio, stock

#### `mesa.py`
- **Clase**: `Mesa`
- **Atributos**: id, numero, estado
- **Métodos**:
  - `esta_disponible()` - Verifica disponibilidad
  - `esta_ocupada()` - Verifica si está ocupada

#### `caja.py`
- **Clase**: `Caja`
- **Atributos**: id, usuario_id, fecha_apertura, fecha_cierre, monto_inicial

#### `venta.py`
- **Clases**: 
  - `Venta` - Encabezado de venta
  - `DetalleVenta` - Detalles por línea
- **Atributos**: id, usuario_id, mesa_id, total, fecha

#### `__init__.py`
- Marca a `models` como paquete

---

## ⚙️ `/app/services/` - Lógica de Negocio

#### `auth_service.py`
- **Clase**: `AuthService`
- **Métodos principales**:
  - `login()` - Autenticación de usuario
  - `logout()` - Cierre de sesión
  - `puede()` - Verifica permisos

#### `permisos.py`
- **Clase**: `Permisos` (enum)
- **Permisos disponibles**:
  - `USAR_MESAS` - Acceso a mesas
  - `VER_PRODUCTOS` - Ver catálogo
  - `ADMINISTRAR_USUARIOS` - Gestión de usuarios
  - `ADMINISTRAR_PRODUCTOS` - Gestión de inventario
  - `CONSULTAR_REPORTES` - Acceso a reportes
  - `MODIFICAR_CONFIGURACION` - Cambiar configuración
  - `ADMINISTRAR_SISTEMA` - Control total

#### `caja_service.py`
- **Funciones**: Apertura/cierre de caja, movimientos

#### `venta_service.py`
- **Funciones**: Crear ventas, agregar detalles, calcular totales

#### `producto_service.py`
- **Funciones**: Gestión de productos e inventario

#### `usuario_service.py`
- **Funciones**: CRUD de usuarios, cambio de contraseña

#### `mesa_service.py`
- **Funciones**: Gestión de mesas, cambio de estado

#### `inventario_service.py`
- **Funciones**: Reportes de stock, movimientos

#### `reporte_service.py`
- **Funciones**: Generación de reportes en Excel

#### `cobro_service.py`
- **Funciones**: Procesamiento de cobros

#### `comprobante_service.py`
- **Funciones**: Generación de comprobantes

#### `configuracion_service.py`
- **Funciones**: Gestión de configuración de la app

#### `config_manager.py`
- **Funciones**: Lectura/escritura de configuración en JSON

#### `backup_service.py`
- **Funciones**: Crear y restaurar backups

#### `system_service.py`
- **Funciones**: Operaciones del sistema, logs

#### `__init__.py`
- Marca a `services` como paquete

---

## 🖥️ `/app/ui/` - Interfaz Gráfica

#### `main_window.py` ⭐ (MODIFICADO)
- **Clase**: `MainWindow`
- **Descripción**: Ventana principal después del login
- **Componentes**:
  - Sidebar de navegación
  - Área de contenido (QStackedWidget)
  - Info de usuario
  - Botones de acción
- **CAMBIO REALIZADO**: Agregado "Licencia de Tech Pixel C" en la sidebar

#### `login_window.py`
- **Clase**: `LoginWindow`
- **Descripción**: Pantalla de autenticación
- **Campos**: Usuario, Contraseña
- **Validaciones**: Credenciales, campos requeridos

#### `/ui/screens/` - Pantallas de la Aplicación

##### `_base_screen.py`
- **Clase base**: Para todas las pantallas
- **Métodos comunes**: refrescar, validar, etc.

##### `mesas_screen.py`
- Gestión de mesas, pedidos en tiempo real

##### `productos_screen.py`
- Catálogo de productos, búsqueda

##### `usuarios_screen.py`
- CRUD de usuarios (solo admin)

##### `caja_screen.py`
- Apertura/cierre de caja, estado

##### `historial_screen.py`
- Historial de ventas, búsqueda

##### `inventario_screen.py`
- Movimientos de stock (solo admin)

##### `reportes_screen.py`
- Reportes en Excel, gráficos

##### `configuracion_screen.py`
- Configuración general de la app

##### `cobro_screen.py`
- Procesamiento de cobros

##### `github_config_screen.py`
- Configuración de actualizaciones desde GitHub

##### `__init__.py`
- Marca a `screens` como paquete

#### `/ui/widgets/` - Componentes Reutilizables

##### `catalogo_widget.py`
- Widget para mostrar productos

##### `mesa_card.py`
- Tarjeta visual de mesa

##### `dialogo_usuario.py`
- Diálogo para agregar/editar usuario

##### `dialogo_password.py`
- Diálogo para cambiar contraseña

##### `dialogo_domicilio.py`
- Diálogo para datos de envío

##### `__init__.py`
- Marca a `widgets` como paquete

#### `/ui/themes/`

##### `colors.py`
- Constantes de colores (paleta dark mode)

##### `__init__.py`
- Marca a `themes` como paquete

---

## 🖨️ `/app/printing/` - Impresión Térmica

#### `printer_manager.py`
- **Descripción**: Gestión de impresoras disponibles
- **Métodos**: Detectar, seleccionar, probar impresora

#### `ticket_formatter.py`
- **Descripción**: Formato de tickets para imprimir
- **Métodos**: Generar contenido, alinear texto

#### `escpos.py`
- **Descripción**: Protocolo ESC-POS para impresoras térmicas
- **Métodos**: Enviar comandos, caracteres especiales

#### `__init__.py`
- Marca a `printing` como paquete

---

## 🛠️ `/app/utils/` - Utilidades

#### `logger.py`
- **Descripción**: Sistema de logging
- **Funciones**: `configurar_logger()`, `get_logger()`
- **Archivos de log**: `logs/app.log`

#### `decorators.py`
- Decoradores útiles (validación, timing, etc.)

#### `helpers.py`
- Funciones auxiliares comunes

#### `__init__.py`
- Marca a `utils` como paquete

---

## 🔄 SISTEMA DE ACTUALIZACIONES

#### `app/updater.py` ⭐
- **Descripción**: Verificación e instalación de actualizaciones
- **Funciones principales**:
  - `check_and_update_with_dialog()` - Verifica y pregunta
  - `obtener_version_remota()` - Obtiene versión de GitHub
  - `descargar_ejecutable()` - Descarga el .exe
  - `instalar_actualizacion()` - Reemplaza binario y reinicia
- **Fuente**: `version.json` en GitHub
- **Procedimiento**:
  1. Al iniciar app, lee `version.json` de GitHub
  2. Compara con versión local (`version.json`)
  3. Si hay versión nueva, descarga .exe
  4. Cierra app y ejecuta instalador
  5. Inicia nueva versión

---

## 🔐 `/app/assets/` - Recursos

#### `icon.ico`
- Icono de la aplicación (.ico)
- Usado en: título de ventana, ejecutable

---

## 📁 DIRECTORIOS DE DATOS (NO SE SUBEN)

Estos directorios se excluyen en `.gitignore`:

### `data/`
- `crm.db` - Base de datos SQLite (datos reales)
- `crm.db-shm` - Archivos temporales de SQLite
- `crm.db-wal` - Journal de transacciones

### `backups/`
- `*.db` - Respaldos de base de datos
- `*.zip` - Compresión de backups

### `logs/`
- `app.log` - Log de ejecución

### `reportes/`
- `*.xlsx` - Archivos Excel generados

### `comprobantes/`
- `*.pdf` - Comprobantes generados
- `*.txt` - Recibos de prueba

### `configuracion/`
- `settings.json` - Configuración sensible

---

## 🚫 ARCHIVOS EXCLUIDOS (NO SE SUBEN)

### Compilados y Builds
- `dist/` - Ejecutables compilados
- `build/` - Archivos de compilación
- `*.spec` - Archivos de PyInstaller
- `__pycache__/` - Bytecode compilado
- `*.pyc`, `*.pyo`, `*.pyd` - Archivos compilados

### Directorios Especiales
- `.git/` - Historial de Git
- `.vscode/` - Configuración de VS Code
- `.idea/` - Configuración de PyCharm
- `node_modules/` - Dependencias npm (si las hay)

### Instaladores (Generados)
- `*.exe` - Ejecutables compilados
- `*.msi` - Instaladores
- `*.bat`, `*.ps1` - Scripts de construcción

### Archivos Temporales
- `Thumbs.db` - Cache de Windows
- `.env` - Variables de entorno sensibles

---

## 📊 ESTRUCTURA VISUAL COMPLETA

```
CRM/
│
├── 📄 main.py ⭐ (PUNTO DE ENTRADA)
├── 📄 README.md ⭐ (DOCUMENTACIÓN GENERAL)
├── 📄 requirements.txt ⭐ (DEPENDENCIAS)
├── 📄 version.json ⭐ (VERSIÓN ACTUAL)
├── 📄 .gitignore ⭐ (QUÉ NO SE SUBE)
├── 📄 DOCUMENTACION.md
├── 📄 GITHUB_SETUP.md
├── 📄 ACTUALIZACION.md
├── 📄 ARCHIVOS_GITHUB.md (ESTE ARCHIVO)
│
├── 📂 app/ ⭐ (CÓDIGO PRINCIPAL)
│   ├── __init__.py
│   ├── updater.py ⭐ (ACTUALIZACIONES)
│   │
│   ├── 📂 database/
│   │   ├── connection.py
│   │   ├── migrations.py
│   │   ├── seeder.py
│   │   └── __init__.py
│   │
│   ├── 📂 models/
│   │   ├── usuario.py
│   │   ├── producto.py
│   │   ├── mesa.py
│   │   ├── caja.py
│   │   ├── venta.py
│   │   └── __init__.py
│   │
│   ├── 📂 services/
│   │   ├── auth_service.py
│   │   ├── permisos.py
│   │   ├── usuario_service.py
│   │   ├── producto_service.py
│   │   ├── mesa_service.py
│   │   ├── venta_service.py
│   │   ├── caja_service.py
│   │   ├── inventario_service.py
│   │   ├── reporte_service.py
│   │   ├── comprobante_service.py
│   │   ├── cobro_service.py
│   │   ├── configuracion_service.py
│   │   ├── config_manager.py
│   │   ├── backup_service.py
│   │   ├── system_service.py
│   │   └── __init__.py
│   │
│   ├── 📂 ui/
│   │   ├── main_window.py ⭐ (MODIFICADO)
│   │   ├── login_window.py
│   │   │
│   │   ├── 📂 screens/
│   │   │   ├── _base_screen.py
│   │   │   ├── mesas_screen.py
│   │   │   ├── productos_screen.py
│   │   │   ├── usuarios_screen.py
│   │   │   ├── caja_screen.py
│   │   │   ├── historial_screen.py
│   │   │   ├── inventario_screen.py
│   │   │   ├── reportes_screen.py
│   │   │   ├── configuracion_screen.py
│   │   │   ├── cobro_screen.py
│   │   │   ├── github_config_screen.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── 📂 widgets/
│   │   │   ├── catalogo_widget.py
│   │   │   ├── mesa_card.py
│   │   │   ├── dialogo_usuario.py
│   │   │   ├── dialogo_password.py
│   │   │   ├── dialogo_domicilio.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── 📂 themes/
│   │   │   ├── colors.py
│   │   │   └── __init__.py
│   │   │
│   │   └── (otros archivos UI)
│   │
│   ├── 📂 printing/
│   │   ├── printer_manager.py
│   │   ├── ticket_formatter.py
│   │   ├── escpos.py
│   │   └── __init__.py
│   │
│   ├── 📂 utils/
│   │   ├── logger.py
│   │   ├── decorators.py
│   │   ├── helpers.py
│   │   └── __init__.py
│   │
│   └── 📂 assets/
│       └── icon.ico
│
├── 📂 data/ 🚫 (NO SE SUBE)
│   └── crm.db
│
├── 📂 backups/ 🚫 (NO SE SUBE)
│
├── 📂 logs/ 🚫 (NO SE SUBE)
│
├── 📂 reportes/ 🚫 (NO SE SUBE)
│
└── 📂 comprobantes/ 🚫 (NO SE SUBE)
```

---

## 🔄 ARCHIVOS QUE SE MODIFICAN CON ACTUALIZACIONES

Cuando hagas un cambio y quieras actualizar:

1. **Modifica el código** en los archivos del proyecto
2. **Actualiza `version.json`** con nueva versión
3. **Haz commit**: `git add . && git commit -m "v1.1 - Description"`
4. **Sube cambios**: `git push origin main`
5. **Crea Release en GitHub** con el nuevo `.exe`

---

## 📝 RESUMEN DE CAMBIOS REALIZADOS

### ✨ Cambio Actual (v1.0.1)
- **Archivo**: `app/ui/main_window.py`
- **Modificación**: Se agregó "Licencia de Tech Pixel C" en la sidebar
- **Ubicación**: Parte inferior, debajo del botón "Cerrar sesión"
- **Estilo**: Discreto, alineado con el diseño oscuro
- **Propósito**: Prueba del sistema de actualizaciones

---

## 🎯 PRÓXIMOS PASOS PARA GIT

### 1. Hacer commit del cambio
```bash
git add app/ui/main_window.py
git commit -m "Add Tech Pixel C license text v1.0.1"
```

### 2. Actualizar version.json
```bash
# Cambiar en version.json:
{
  "version": "1.0.1",
  "release_date": "2026-09-23"
}
```

### 3. Subir a GitHub
```bash
git add version.json
git commit -m "Update version to 1.0.1"
git push origin main
```

### 4. Crear Release en GitHub
- Ir a Releases → New Release
- Tag: `v1.0.1`
- Adjuntar archivo `.exe` compilado
- Descripción: "Minor update - Added Tech Pixel C license"

---

## ✅ CHECKLIST PARA UPLOAD A GITHUB

- [ ] Todos los archivos fuente están en `/app/`
- [ ] `main.py` está en raíz
- [ ] `requirements.txt` actualizado con dependencias
- [ ] `version.json` actualizado con nueva versión
- [ ] `.gitignore` correctamente configurado
- [ ] README.md está actualizado
- [ ] Documentación técnica (DOCUMENTACION.md) existe
- [ ] No hay archivos `.db` o logs en el repo
- [ ] No hay carpeta `dist/` o `build/`
- [ ] Cambios confirmados con `git commit`
- [ ] Cambios pusheados con `git push`
- [ ] Release creado en GitHub con `.exe`

---

## 📌 NOTAS IMPORTANTES

1. **Base de datos local**: Cada máquina tiene su propia `data/crm.db`
2. **No versionar datos**: Los archivos de datos NUNCA se suben a GitHub
3. **Configuración local**: Cada usuario puede tener su `configuracion/settings.json`
4. **Logs locales**: Los logs se generan solo en desarrollo
5. **Binarios compilados**: Se crean en `dist/` pero NO se versionan en Git

---

**Documento generado**: 2026-09-23  
**Versión del Proyecto**: 1.0.1  
**Estado**: Listo para GitHub ✅
