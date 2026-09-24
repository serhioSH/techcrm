@echo off
REM ============================================================
REM TECHCRM POS - Instalador v3.0
REM Compatible con Windows 10 y 11
REM ============================================================

echo.
echo ========================================
echo  TECHCRM POS - Instalador v3.0
echo ========================================
echo.
echo Iniciando instalacion...
echo.

REM Verificar si se está ejecutando como administrador
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo ERROR: Se requieren permisos de administrador.
    echo.
    echo Haz click derecho en este archivo y selecciona
    echo "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

REM Ejecutar el script PowerShell
PowerShell.exe -ExecutionPolicy Bypass -File "%~dp0Instalador_v3.ps1"

exit /b %errorlevel%
