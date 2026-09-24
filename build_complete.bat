@echo off
REM ============================================================
REM Script completo de construcción e instalación para TCRM
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ===============================================
echo   CONSTRUCCIÓN COMPLETA DE TCRM v1.0
echo   Sistema POS para Comidas Rápidas
echo ===============================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    pause
    exit /b 1
)

echo [1/5] Limpiando directorios...
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1
echo ✓ Limpios

echo.
echo [2/5] Instalando PyInstaller...
pip install pyinstaller >nul 2>&1
echo ✓ PyInstaller listo

echo.
echo [3/5] Compilando aplicación con PyInstaller...
pyinstaller --onedir --windowed --icon=app\assets\icon.ico ^
    --add-data "app;app" ^
    --add-data "requirements.txt;." ^
    --add-data "versioninfo.json;." ^
    --name TCRM ^
    main.py

if errorlevel 1 (
    echo ERROR: Compilación falló
    pause
    exit /b 1
)
echo ✓ Compilación completada

echo.
echo [4/5] Verificando archivos compilados...
if not exist "dist\TCRM\TCRM.exe" (
    echo ERROR: TCRM.exe no encontrado
    pause
    exit /b 1
)
echo ✓ TCRM.exe generado correctamente

echo.
echo [5/5] Buscando NSIS para crear instalador...
set "NSIS_PATH=C:\Program Files (x86)\NSIS\makensis.exe"
set "NSIS_PATH_ALT=C:\Program Files\NSIS\makensis.exe"

if exist "!NSIS_PATH!" (
    echo ✓ NSIS encontrado
    echo.
    echo Generando instalador...
    "!NSIS_PATH!" TCRM_installer.nsi
    if errorlevel 1 (
        echo ERROR: NSIS falló
        pause
        exit /b 1
    )
    echo ✓ Instalador generado: TCRM_Setup.exe
) else if exist "!NSIS_PATH_ALT!" (
    echo ✓ NSIS encontrado
    echo.
    echo Generando instalador...
    "!NSIS_PATH_ALT!" TCRM_installer.nsi
    if errorlevel 1 (
        echo ERROR: NSIS falló
        pause
        exit /b 1
    )
    echo ✓ Instalador generado: TCRM_Setup.exe
) else (
    echo ! NSIS no está instalado
    echo ! Puedes descargar desde: https://nsis.sourceforge.io/
    echo ! Por ahora, la aplicación compilada está lista en:
    echo ! %CD%\dist\TCRM\TCRM.exe
)

echo.
echo ===============================================
echo   ✓ CONSTRUCCIÓN COMPLETADA EXITOSAMENTE
echo ===============================================
echo.
echo RESULTADOS:
echo.
echo 1. Ejecutable compilado:
echo    %CD%\dist\TCRM\TCRM.exe
echo.
if exist "TCRM_Setup.exe" (
    echo 2. Instalador creado:
    echo    %CD%\TCRM_Setup.exe
    echo.
) else (
    echo 2. Instalador:
    echo    Para crear el instalador, instala NSIS y ejecuta:
    echo    makensis TCRM_installer.nsi
    echo.
)
echo Datos guardados en:
echo    - Base de datos: app\data\
echo    - Configuración: app\configuracion\
echo    - Logos: app\configuracion\logos\
echo    - Reportes: reportes\
echo    - Comprobantes: comprobantes\
echo.
echo ===============================================
echo.

pause
