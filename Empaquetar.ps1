# ============================================================
# SCRIPT DE EMPAQUETADO FINAL - TECHCRM POS
# ============================================================
# Este script crea el paquete final de distribucion

param(
    [switch]$SkipVerification = $false,
    [switch]$NoCleanup = $false
)

# ============================================================
# FUNCIONES
# ============================================================

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[AVISO] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# ============================================================
# VERIFICACIONES INICIALES
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host "EMPAQUETADOR - TECHCRM POS v1.0.0"
Write-Host "============================================================"
Write-Host ""

Write-Info "Iniciando empaquetado..."
Write-Info ""

# Verificar archivos necesarios
Write-Info "Verificando archivos necesarios..."

$requiredFiles = @(
    "dist\TECHCRM-POS\TECHCRM-POS.exe",
    "dist\TECHCRM-POS\_internal",
    "Instalar.bat",
    "diagnostico.py"
)

$allExists = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  OK $file" -ForegroundColor Green
    } else {
        Write-Host "  ERROR $file (NO ENCONTRADO)" -ForegroundColor Red
        $allExists = $false
    }
}

if (-not $allExists) {
    Write-Error-Custom "Algunos archivos requeridos no existen"
    exit 1
}

Write-Success "Todos los archivos verificados"
Write-Host ""

# ============================================================
# CREAR DIRECTORIO DE EMPAQUETADO
# ============================================================

Write-Info "Preparando directorio de empaquetado..."

$stagingDir = "TECHCRM-POS-Release"
$packageName = "TECHCRM-POS-Windows-x64-v1.0.0"
$zipPath = "$packageName.zip"

# Limpiar si existe
if (Test-Path $stagingDir) {
    Write-Warning "Eliminando directorio anterior..."
    Remove-Item -Path $stagingDir -Recurse -Force
}

# Crear estructura
New-Item -ItemType Directory -Path $stagingDir | Out-Null
Write-Success "Directorio de staging creado: $stagingDir"

Write-Host ""

# ============================================================
# COPIAR ARCHIVOS AL STAGING
# ============================================================

Write-Info "Copiando archivos de distribucion..."

# Copiar compilado
Write-Info "  -> Copiando aplicacion compilada..."
Copy-Item -Path "dist\TECHCRM-POS" -Destination "$stagingDir\TECHCRM-POS" -Recurse
Write-Host "    OK Aplicacion copiada"

# Copiar instalador
Write-Info "  -> Copiando instalador..."
Copy-Item -Path "Instalar.bat" -Destination "$stagingDir\Instalar.bat"
Write-Host "    OK Instalador copiado"

# Copiar diagnóstico
Write-Info "  -> Copiando herramienta de diagnostico..."
Copy-Item -Path "diagnostico.py" -Destination "$stagingDir\diagnostico.py"
Write-Host "    OK Diagnostico copiado"

# Crear archivo README.txt
Write-Info "  -> Generando documentacion..."

$readmeContent = @"
TECHCRM POS v1.0.0 - PAQUETE DE DISTRIBUCION WINDOWS

Bienvenido a TECHCRM POS!

Este paquete contiene TECHCRM POS v1.0.0, un sistema profesional
de Punto de Venta (POS) diseñado para restaurantes y comidas
rápidas.

════════════════════════════════════════════════════════════════

CONTENIDO DEL PAQUETE

  * TECHCRM-POS/           - Aplicacion compilada (lista para usar)
  * Instalar.bat           - Script de instalacion
  * diagnostico.py         - Herramienta de diagnostico
  * README.txt             - Este archivo

════════════════════════════════════════════════════════════════

REQUISITOS DEL SISTEMA

  * Windows 10 o superior (64 bits)
  * Minimo 500 MB de espacio libre en disco
  * Permisos de administrador para instalar

════════════════════════════════════════════════════════════════

INSTALACION RAPIDA

  1. Abre este archivo en la carpeta extraída:
     Instalar.bat

  2. Haz doble clic

  3. Haz clic en SI cuando te pida permisos de administrador

  4. Sigue las instrucciones en pantalla

  5. Listo! TECHCRM POS estará instalado

════════════════════════════════════════════════════════════════

CREDENCIALES POR DEFECTO

  Usuario:     techcrm
  Contraseña:  1234567

  IMPORTANTE: Cambia la contraseña en tu primer acceso
  (Configuracion -> Identidad -> Admin)

════════════════════════════════════════════════════════════════

CARACTERISTICAS

  OK Gestion de mesas y pedidos
  OK Catalogo dinamico de productos
  OK Procesamiento de pagos (Efectivo, Transferencia)
  OK Impresion de comprobantes en termica
  OK Reportes de ventas
  OK Gestion de usuarios con roles
  OK Control de caja
  OK Base de datos SQLite local

════════════════════════════════════════════════════════════════

HERRAMIENTAS INCLUIDAS

  * TECHCRM-POS-Diagnostico.exe
    Herramienta para verificar que todo está correctamente
    instalado y configurado.

════════════════════════════════════════════════════════════════

UBICACION DESPUES DE INSTALAR

  C:\Program Files\TECHCRM POS\

Desde aquí puedes:
  * Ejecutar la aplicacion
  * Acceder a la herramienta de diagnostico
  * Desinstalar la aplicacion

════════════════════════════════════════════════════════════════

VERIFICACION POST-INSTALACION

Después de instalar, verifica que:

  OK TECHCRM POS aparece en el menu de inicio
  OK Hay un acceso directo en el escritorio
  OK Puedes iniciar sesion con techcrm/1234567
  OK La aplicacion responde correctamente

════════════════════════════════════════════════════════════════

DESINSTALACION

Para desinstalar TECHCRM POS:

  Opcion 1: Panel de Control
    Panel de Control -> Programas -> Programas y características
    Busca TECHCRM POS y haz clic en Desinstalar

  Opcion 2: Desde la carpeta de instalacion
    C:\Program Files\TECHCRM POS\Desinstalar_TECHCRM.bat

════════════════════════════════════════════════════════════════

INFORMACION DE VERSION

  Version:       1.0.0
  Tipo:          Aplicacion de Escritorio (PySide6/Qt)
  Base de Datos: SQLite local
  Plataforma:    Windows 10+ (64 bits)
  Tamaño:        Aproximadamente 500 MB

════════════════════════════════════════════════════════════════

Gracias por usar TECHCRM POS.

Copyright 2026 TECHCRM Systems
Todos los derechos reservados.

════════════════════════════════════════════════════════════════
"@

$readmeContent | Out-File -FilePath "$stagingDir\README.txt" -Encoding UTF8
Write-Host "    OK Documentacion generada"

Write-Success "Todos los archivos copiados al staging"
Write-Host ""

# ============================================================
# CALCULAR TAMAÑO
# ============================================================

Write-Info "Calculando tamaño del paquete..."

$stagingSize = (Get-ChildItem -Path $stagingDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Info "  Tamaño total: $([math]::Round($stagingSize, 2)) MB"

Write-Host ""

# ============================================================
# CREAR ZIP
# ============================================================

Write-Info "Creando archivo ZIP..."

# Eliminar ZIP anterior si existe
if (Test-Path $zipPath) {
    Write-Warning "Eliminando ZIP anterior..."
    Remove-Item -Path $zipPath -Force
}

# Crear ZIP
Add-Type -AssemblyName System.IO.Compression.FileSystem

try {
    [System.IO.Compression.ZipFile]::CreateFromDirectory(
        (Resolve-Path $stagingDir).Path,
        (Resolve-Path ".").Path + "\$zipPath",
        [System.IO.Compression.CompressionLevel]::Optimal,
        $false
    )
    Write-Success "ZIP creado exitosamente"
} catch {
    Write-Error-Custom "Error al crear ZIP: $_"
    exit 1
}

Write-Host ""

# ============================================================
# VERIFICAR ZIP
# ============================================================

Write-Info "Verificando ZIP..."

if (Test-Path $zipPath) {
    $zipSize = (Get-Item $zipPath).Length / 1MB
    Write-Success "ZIP verificado ($([math]::Round($zipSize, 2)) MB)"
    
    # Listar contenido
    Write-Info "Contenido del ZIP:"
    
    $zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
    $zip.Entries | Select-Object -First 10 | ForEach-Object {
        Write-Host "  * $($_.FullName)"
    }
    
    if ($zip.Entries.Count -gt 10) {
        Write-Host "  ... y $($zip.Entries.Count - 10) mas"
    }
    
    $zip.Dispose()
} else {
    Write-Error-Custom "ZIP no se creo correctamente"
    exit 1
}

Write-Host ""

# ============================================================
# LIMPIAR (OPCIONAL)
# ============================================================

if (-not $NoCleanup) {
    Write-Info "Limpiando directorio de staging..."
    Remove-Item -Path $stagingDir -Recurse -Force
    Write-Success "Directorio de staging eliminado"
}

Write-Host ""

# ============================================================
# RESUMEN FINAL
# ============================================================

Write-Host "============================================================"
Write-Host "OK EMPAQUETADO COMPLETADO EXITOSAMENTE"
Write-Host "============================================================"
Write-Host ""
Write-Host "ARCHIVO FINAL:"
Write-Host "   $zipPath"
Write-Host ""
Write-Host "TAMAÑO:"
Write-Host "   $([math]::Round($zipSize, 2)) MB"
Write-Host ""
Write-Host "CONTENIDO:"
Write-Host "   * TECHCRM-POS/        (aplicacion compilada)"
Write-Host "   * Instalar.bat        (script de instalacion)"
Write-Host "   * diagnostico.py      (herramienta de diagnostico)"
Write-Host "   * README.txt          (documentacion)"
Write-Host ""
Write-Host "PARA DISTRIBUIR:"
Write-Host "   Comparte el archivo: $zipPath"
Write-Host ""
Write-Host "PARA INSTALAR:"
Write-Host "   1. Extrae el ZIP"
Write-Host "   2. Abre la carpeta"
Write-Host "   3. Ejecuta: Instalar.bat"
Write-Host "   4. Haz clic en SI para admin"
Write-Host ""
Write-Host "============================================================"
Write-Host ""

exit 0
