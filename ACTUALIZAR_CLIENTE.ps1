# ============================================================
# SCRIPT DE ACTUALIZACIÓN PARA CLIENTES (PowerShell)
# Descarga el nuevo .exe y reemplaza el antiguo
# CONSERVA: Base de datos, configuración, reportes, etc.
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TECHCRM - Actualización del Sistema" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Validar que estamos en la carpeta correcta
if (-not (Test-Path "TECHCRM-POS.exe")) {
    Write-Host "ERROR: Este script debe ejecutarse en la carpeta donde está TECHCRM-POS.exe" -ForegroundColor Red
    Write-Host ""
    Write-Host "Ejemplo:" -ForegroundColor Yellow
    Write-Host "  C:\Users\USUARIO\AppData\Local\Programs\TECHCRM\" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Presiona Enter para cerrar"
    exit 1
}

try {
    Write-Host "[1/4] Verificando conexión a internet..." -ForegroundColor Yellow
    $connection = Test-Connection github.com -Count 1 -ErrorAction SilentlyContinue
    if (-not $connection) {
        Write-Host "ERROR: No hay conexión a internet" -ForegroundColor Red
        Write-Host "Por favor, verifica tu conexión y vuelve a intentar" -ForegroundColor Red
        Read-Host "Presiona Enter para cerrar"
        exit 1
    }
    Write-Host "OK - Conexión disponible" -ForegroundColor Green

    Write-Host ""
    Write-Host "[2/4] Creando respaldo del ejecutable actual..." -ForegroundColor Yellow
    
    # Crear carpeta de backup
    if (-not (Test-Path "backups")) {
        New-Item -ItemType Directory -Path "backups" -Force | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd-HH-mm-ss"
    $backupFile = "backups\TECHCRM-POS-$timestamp.exe"
    Copy-Item "TECHCRM-POS.exe" $backupFile -Force
    Write-Host "OK - Respaldo creado en: $backupFile" -ForegroundColor Green

    Write-Host ""
    Write-Host "[3/4] Descargando nueva versión..." -ForegroundColor Yellow
    Write-Host "Descargando desde: https://github.com/serhioSH/techcrm/releases/download/v1.0.1/TECHCRM-POS.exe" -ForegroundColor Gray
    
    $downloadUrl = "https://github.com/serhioSH/techcrm/releases/download/v1.0.1/TECHCRM-POS.exe"
    $tempFile = "TECHCRM-POS-NEW.exe"
    
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempFile -TimeoutSec 300
    
    if (-not (Test-Path $tempFile)) {
        Write-Host "ERROR: No se pudo descargar el nuevo ejecutable" -ForegroundColor Red
        Read-Host "Presiona Enter para cerrar"
        exit 1
    }
    
    Write-Host "OK - Descarga completada" -ForegroundColor Green

    Write-Host ""
    Write-Host "[4/4] Instalando actualización..." -ForegroundColor Yellow
    Write-Host "Deteniendo la aplicación actual..." -ForegroundColor Gray
    
    # Cerrar la aplicación si está en ejecución
    Get-Process "TECHCRM-POS" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process "main" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    # Esperar un poco
    Start-Sleep -Seconds 2
    
    Write-Host "Reemplazando ejecutable..." -ForegroundColor Gray
    Remove-Item "TECHCRM-POS.exe" -Force
    Move-Item $tempFile "TECHCRM-POS.exe" -Force
    
    Write-Host "OK - Ejecutable actualizado" -ForegroundColor Green

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "   ACTUALIZACIÓN COMPLETADA EXITOSAMENTE" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Base de datos:     CONSERVADA ✓" -ForegroundColor Green
    Write-Host "Configuración:     CONSERVADA ✓" -ForegroundColor Green
    Write-Host "Productos:         CONSERVADA ✓" -ForegroundColor Green
    Write-Host "Inventario:        CONSERVADA ✓" -ForegroundColor Green
    Write-Host "Reportes:          CONSERVADA ✓" -ForegroundColor Green
    Write-Host ""
    Write-Host "La aplicación se iniciará en 3 segundos..." -ForegroundColor Yellow
    Write-Host ""
    
    Start-Sleep -Seconds 3
    
    Write-Host "Iniciando TECHCRM..." -ForegroundColor Gray
    Start-Process "TECHCRM-POS.exe"
    
    Write-Host ""
    Write-Host "ACTUALIZACIÓN FINALIZADA" -ForegroundColor Green
    Write-Host "Cierra esta ventana para continuar" -ForegroundColor Yellow
    Write-Host ""

}
catch {
    Write-Host ""
    Write-Host "ERROR: " $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    
    # Intentar restaurar respaldo
    if (Test-Path $backupFile) {
        Write-Host "Restaurando respaldo..." -ForegroundColor Yellow
        Copy-Item $backupFile "TECHCRM-POS.exe" -Force
        Write-Host "Respaldo restaurado" -ForegroundColor Green
    }
    
    Read-Host "Presiona Enter para cerrar"
    exit 1
}

Read-Host "Presiona Enter para cerrar"
