@echo off
REM ============================================================
REM SCRIPT DE DIAGNÓSTICO
REM ============================================================

echo.
echo ============================================================
echo   TECHCRM - Diagnóstico del Sistema
echo ============================================================
echo.

echo [1/3] Buscando archivo de log...
if exist "logs" (
    echo OK - Carpeta logs encontrada
    echo.
    echo [2/3] Mostrando últimas líneas del log...
    echo.
    
    REM Obtener el archivo de log más reciente
    for /f "tokens=*" %%A in ('dir /B /O-D "logs\*.log" 2^>nul') do (
        set "LATEST_LOG=logs\%%A"
        goto :found
    )
    
    :found
    if defined LATEST_LOG (
        echo Log file: !LATEST_LOG!
        echo.
        echo ============================================================
        type "!LATEST_LOG!"
        echo ============================================================
    ) else (
        echo ERROR: No se encontraron archivos de log
    )
) else (
    echo ERROR: Carpeta logs no encontrada
    echo Por favor, ejecuta la aplicación primero
)

echo.
echo [3/3] Copia este contenido y envíalo al desarrollador
echo.
pause
