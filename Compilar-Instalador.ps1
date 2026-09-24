# ============================================================
# SCRIPT PARA COMPILAR INSTALADOR DE TECHCRM POS
# ============================================================
# Este script compila el archivo Instalar.iss con Inno Setup
# para generar el ejecutable del instalador.
#
# Uso:
#   PowerShell -ExecutionPolicy Bypass -File Compilar-Instalador.ps1
# ============================================================

param(
    [switch]$SkipCompilation = $false,
    [switch]$ShowLog = $false
)

# ============================================================
# FUNCIONES AUXILIARES
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

function Get-ISSPath {
    # Buscar Inno Setup en ubicaciones comunes
    $possiblePaths = @(
        "C:\Program Files (x86)\Inno Setup 6\iscc.exe",
        "C:\Program Files\Inno Setup 6\iscc.exe",
        "C:\Program Files (x86)\Inno Setup 5\iscc.exe",
        "C:\Program Files\Inno Setup 5\iscc.exe"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    # Intentar encontrarlo en el PATH
    $iscc = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($iscc) {
        return $iscc.Source
    }
    
    return $null
}

# ============================================================
# INICIO DEL SCRIPT
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host "COMPILADOR DE INSTALADOR - TECHCRM POS"
Write-Host "============================================================"
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "Instalar.iss")) {
    Write-Error-Custom "Instalar.iss no encontrado en el directorio actual"
    Write-Info "Por favor ejecuta este script desde: c:\Users\duvan\OneDrive\Desktop\sergio\CRM"
    exit 1
}

Write-Success "Directorio correcto confirmado"

# ============================================================
# BÚSQUEDA DE INNO SETUP
# ============================================================

Write-Info "Buscando Inno Setup..."

$isccPath = Get-ISSPath

if ($isccPath) {
    Write-Success "Inno Setup encontrado: $isccPath"
} else {
    Write-Error-Custom "Inno Setup no está instalado"
    Write-Info ""
    Write-Info "Para instalar Inno Setup:"
    Write-Info "  1. Descarga desde: https://jrsoftware.org/isdl.php"
    Write-Info "  2. Ejecuta el instalador"
    Write-Info "  3. Vuelve a ejecutar este script"
    Write-Info ""
    Write-Warning "¿Deseas descargar Inno Setup? (abriendo navegador)"
    Write-Warning "Puedes también hacer clic 'No' y continuar sin compilar el .iss"
    
    # Preguntar si descargar
    $response = Read-Host "¿Descargar Inno Setup? (S/N)"
    
    if ($response -eq "S" -or $response -eq "s") {
        Start-Process "https://jrsoftware.org/isdl.php"
        Write-Info "Se abrió el navegador. Por favor instala Inno Setup y vuelve a ejecutar este script."
        exit 1
    } else {
        Write-Warning "Inno Setup es necesario para compilar el instalador profesional."
        Write-Warning "Continuando sin compilar (se usará instalador alternativo)"
        exit 0
    }
}

# ============================================================
# COMPILACIÓN
# ============================================================

Write-Info "Compilando Instalar.iss..."
Write-Info ""

# Crear directorio de output si no existe
if (-not (Test-Path "Output")) {
    New-Item -ItemType Directory -Path "Output" | Out-Null
}

# Ejecutar iscc
$startTime = Get-Date

& $isccPath Instalar.iss

$exitCode = $LASTEXITCODE
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Info ""

if ($exitCode -eq 0) {
    Write-Success "Compilación completada ($($duration.TotalSeconds.ToString('F1'))s)"
    
    # Verificar que se creó el instalador
    if (Test-Path "Output\Instalar.exe") {
        $fileSize = (Get-Item "Output\Instalar.exe").Length / 1MB
        Write-Success "Instalar.exe creado ($([math]::Round($fileSize, 2)) MB)"
        Write-Info ""
        Write-Info "El instalador está listo en: Output\Instalar.exe"
        Write-Info ""
        Write-Host "============================================================"
        Write-Host "✅ COMPILACIÓN EXITOSA"
        Write-Host "============================================================"
        Write-Host ""
        exit 0
    } else {
        Write-Error-Custom "Instalar.exe no se creó"
        exit 1
    }
} else {
    Write-Error-Custom "La compilación falló con código de salida: $exitCode"
    
    if ($ShowLog) {
        Write-Info ""
        Write-Info "Revisar Output\Setup Log.txt para más detalles"
    }
    
    exit $exitCode
}

