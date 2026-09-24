@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ===================================================================
REM INSTALADOR TECHCRM - VERSION BATCH PURO
REM ===================================================================

echo.
echo ========================================
echo   INSTALADOR TECHCRM v1.0
echo ========================================
echo.

REM Verificar privilegios de administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Debes ejecutar como Administrador
    echo.
    echo Haz clic derecho y selecciona "Ejecutar como administrador"
    pause
    exit /b 1
)

REM Definir rutas
set "INSTALL_DIR=C:\TECHCRM"
set "DATA_DIR=%LOCALAPPDATA%\TECHCRM"
set "SOURCE_DIR=%~dp0"

REM Buscar ejecutable
set "EXE_SOURCE="
if exist "%SOURCE_DIR%TECHCRM.exe" (
    set "EXE_SOURCE=%SOURCE_DIR%TECHCRM.exe"
) else if exist "%SOURCE_DIR%dist\TECHCRM.exe" (
    set "EXE_SOURCE=%SOURCE_DIR%dist\TECHCRM.exe"
) else (
    echo ERROR: No se encontro TECHCRM.exe
    pause
    exit /b 1
)

echo [1/6] Preparando directorios...
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%" >nul 2>&1
mkdir "%INSTALL_DIR%" 2>nul
mkdir "%DATA_DIR%" 2>nul
mkdir "%DATA_DIR%\comprobantes" 2>nul
mkdir "%DATA_DIR%\reportes" 2>nul
mkdir "%DATA_DIR%\backups" 2>nul
mkdir "%DATA_DIR%\logs" 2>nul

echo [2/6] Copiando archivos...
copy /Y "!EXE_SOURCE!" "%INSTALL_DIR%\TECHCRM.exe" >nul
if %errorlevel% neq 0 (
    echo ERROR: No se pudo copiar el ejecutable
    pause
    exit /b 1
)

if exist "%SOURCE_DIR%versioninfo.json" (
    copy /Y "%SOURCE_DIR%versioninfo.json" "%INSTALL_DIR%\versioninfo.json" >nul
)

echo [3/6] Creando configuracion...
echo {"first_run": true} > "%INSTALL_DIR%\config.json"

echo [4/6] Registrando en Windows...
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM" /v DisplayName /t REG_SZ /d "TECHCRM - Sistema POS" /f >nul 2>&1
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM" /v DisplayVersion /t REG_SZ /d "1.0.0" /f >nul 2>&1
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM" /v InstallLocation /t REG_SZ /d "%INSTALL_DIR%" /f >nul 2>&1

echo [5/6] Creando desinstalador...
(
echo @echo off
echo taskkill /f /im TECHCRM.exe ^>nul 2^>^&1
echo rmdir /s /q "%INSTALL_DIR%" ^>nul 2^>^&1
echo rmdir /s /q "%DATA_DIR%" ^>nul 2^>^&1
echo reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM" /f ^>nul 2^>^&1
echo echo TECHCRM desinstalado
echo pause
) > "%INSTALL_DIR%\uninstall.bat"

echo [6/6] Creando accesos directos...

REM Crear script VBS para acceso directo en escritorio
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo Set oShellLink = WshShell.CreateShortcut^("%PUBLIC%\Desktop\TECHCRM.lnk"^)
echo oShellLink.TargetPath = "%INSTALL_DIR%\TECHCRM.exe"
echo oShellLink.WindowStyle = 1
echo oShellLink.IconLocation = "%INSTALL_DIR%\TECHCRM.exe, 0"
echo oShellLink.Description = "TECHCRM - Sistema POS"
echo oShellLink.WorkingDirectory = "%INSTALL_DIR%"
echo oShellLink.Save
) > "%TEMP%\techcrm_desktop.vbs"

REM Crear script VBS para menu inicio
mkdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs" 2>nul
(
echo Set WshShell = CreateObject^("WScript.Shell"^)
echo Set oShellLink = WshShell.CreateShortcut^("%APPDATA%\Microsoft\Windows\Start Menu\Programs\TECHCRM.lnk"^)
echo oShellLink.TargetPath = "%INSTALL_DIR%\TECHCRM.exe"
echo oShellLink.WindowStyle = 1
echo oShellLink.IconLocation = "%INSTALL_DIR%\TECHCRM.exe, 0"
echo oShellLink.Description = "TECHCRM - Sistema POS"
echo oShellLink.WorkingDirectory = "%INSTALL_DIR%"
echo oShellLink.Save
) > "%TEMP%\techcrm_startmenu.vbs"

REM Ejecutar scripts
cscript //nologo "%TEMP%\techcrm_desktop.vbs" >nul 2>&1
cscript //nologo "%TEMP%\techcrm_startmenu.vbs" >nul 2>&1
del /f /q "%TEMP%\techcrm_desktop.vbs" >nul 2>&1
del /f /q "%TEMP%\techcrm_startmenu.vbs" >nul 2>&1

echo.
echo ========================================
echo   INSTALACION COMPLETADA
echo ========================================
echo.
echo Ubicacion: %INSTALL_DIR%
echo Datos: %DATA_DIR%
echo.
echo COMO ABRIR TECHCRM:
echo - Doble clic en icono del Escritorio
echo - Buscar "TECHCRM" en Menu Inicio
echo - Ejecutar: %INSTALL_DIR%\TECHCRM.exe
echo.
echo USUARIOS:
echo - admin / admin123
echo - techcrm / techpixelc
echo.
pause
