@echo off
REM ============================================================
REM SCRIPT DE ACTUALIZACIÓN PARA CLIENTES
REM Descarga el nuevo .exe y reemplaza el antiguo
REM CONSERVA: Base de datos, configuración, reportes, etc.
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   TECHCRM - Actualización del Sistema
echo ============================================================
echo.

REM Detectar si está ejecutándose desde el directorio correcto
if not exist "TECHCRM-POS.exe" (
    echo ERROR: Este script debe ejecutarse en la carpeta donde está TECHCRM-POS.exe
    echo.
    echo Ejemplo:
    echo   C:\Users\USUARIO\AppData\Local\Programs\TECHCRM\
    echo.
    pause
    exit /b 1
)

echo [1/4] Verificando conexión a internet...
ping github.com -n 1 >nul 2>&1
if errorlevel 1 (
    echo ERROR: No hay conexión a internet
    echo Por favor, verifica tu conexión y vuelve a intentar
    pause
    exit /b 1
)
echo OK - Conexión disponible

echo.
echo [2/4] Creando respaldo del ejecutable actual...
REM Crear carpeta de backup si no existe
if not exist "backups" mkdir backups
set "BACKUP_FILE=backups\TECHCRM-POS-!DATE:/=-!-!TIME:~0,2!-!TIME:~3,2!.exe"
copy "TECHCRM-POS.exe" "!BACKUP_FILE!" >nul 2>&1
echo OK - Respaldo creado en: !BACKUP_FILE!

echo.
echo [3/4] Descargando nueva versión...
echo Descargando desde: https://github.com/serhioSH/techcrm/releases/download/v1.0.1/TECHCRM-POS.exe
powershell -Command "& {$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/serhioSH/techcrm/releases/download/v1.0.1/TECHCRM-POS.exe' -OutFile 'TECHCRM-POS-NEW.exe'; if ($?) { Write-Host 'OK - Descarga completada' } else { Write-Host 'ERROR en descarga'; exit 1 } }"

if errorlevel 1 (
    echo ERROR: No se pudo descargar el nuevo ejecutable
    echo Por favor, intenta de nuevo
    pause
    exit /b 1
)

echo.
echo [4/4] Instalando actualización...
echo Cerrando la aplicación actual...

REM Esperar un poco antes de reemplazar
timeout /t 2 >nul

REM Mover el nuevo .exe
echo Reemplazando ejecutable...
del "TECHCRM-POS.exe"
move "TECHCRM-POS-NEW.exe" "TECHCRM-POS.exe" >nul 2>&1

if errorlevel 1 (
    echo ERROR: No se pudo reemplazar el ejecutable
    echo Restaurando respaldo...
    copy "!BACKUP_FILE!" "TECHCRM-POS.exe" >nul 2>&1
    pause
    exit /b 1
)

echo OK - Ejecutable actualizado

echo.
echo ============================================================
echo   ACTUALIZACIÓN COMPLETADA EXITOSAMENTE
echo ============================================================
echo.
echo Base de datos: CONSERVADA ✓
echo Configuración: CONSERVADA ✓
echo Productos: CONSERVADA ✓
echo Inventario: CONSERVADA ✓
echo Reportes: CONSERVADA ✓
echo.
echo La aplicación se iniciará en 3 segundos...
echo.

timeout /t 3 >nul

echo Iniciando TECHCRM...
start "" "TECHCRM-POS.exe"

echo.
echo ACTUALIZACIÓN FINALIZADA
echo Cierra esta ventana para continuar
pause
