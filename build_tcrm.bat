@echo off
REM ============================================================
REM Script de compilación para TCRM
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ===============================================
echo   CONSTRUCCIÓN DE TCRM - Sistema POS
echo ===============================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado. Instala Python primero.
    pause
    exit /b 1
)

echo [1/4] Limpiando directorios anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo ✓ Directorios limpios

echo.
echo [2/4] Instalando dependencias necesarias...
pip install --upgrade pip setuptools wheel >nul 2>&1
pip install pyinstaller >nul 2>&1
echo ✓ Dependencias instaladas

echo.
echo [3/4] Compilando con PyInstaller...
pyinstaller --onedir TCRM.spec
if errorlevel 1 (
    echo ERROR: PyInstaller falló
    pause
    exit /b 1
)
echo ✓ Compilación completada

echo.
echo [4/4] Verificando resultados...
if exist "dist\TCRM\TCRM.exe" (
    echo.
    echo ✓ TCRM.exe compilado exitosamente
    echo.
    echo Ubicación: %CD%\dist\TCRM\TCRM.exe
    echo.
    echo ===============================================
    echo   COMPILACIÓN COMPLETADA
    echo ===============================================
    echo.
    echo Próximos pasos:
    echo 1. Instala NSIS desde https://nsis.sourceforge.io/
    echo 2. Ejecuta: makensis TCRM_installer.nsi
    echo 3. Se generará: TCRM_Setup.exe
    echo.
) else (
    echo ERROR: TCRM.exe no encontrado
    pause
    exit /b 1
)

pause
