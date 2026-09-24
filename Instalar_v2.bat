@echo off
REM ============================================================
REM TECHCRM POS v2.0 - INSTALADOR WINDOWS (MEJORADO)
REM ============================================================
REM Instalador flexible que funciona desde ZIP extraído
REM ============================================================
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
cls

REM ============================================================
REM 1. VERIFICAR PERMISOS DE ADMINISTRADOR
REM ============================================================
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║                  TECHCRM POS - INSTALADOR v2.0             ║
echo ║              Sistema POS para Comidas Rápidas              ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
net session >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Este instalador requiere permisos de administrador.
    echo.
    echo Presiona cualquier tecla para reintentar con permisos elevados...
    pause >nul
    PowerShell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)
echo [OK] Permisos de administrador confirmados
echo.

REM ============================================================
REM 2. DETECTAR CARPETA DE ORIGEN (TECHCRM-POS con exe)
REM ============================================================
set "SOURCE_DIR="
set "CURRENT_DIR=%cd%"

REM Opción 1: Buscar TECHCRM-POS en el mismo directorio del instalador
if exist "%~dp0TECHCRM-POS\TECHCRM-POS.exe" (
    set "SOURCE_DIR=%~dp0TECHCRM-POS"
    echo [OK] Encontrado en: !SOURCE_DIR!
    goto :found_source
)

REM Opción 2: Buscar dist\TECHCRM-POS (si se ejecuta desde el proyecto)
if exist "%CURRENT_DIR%\dist\TECHCRM-POS\TECHCRM-POS.exe" (
    set "SOURCE_DIR=%CURRENT_DIR%\dist\TECHCRM-POS"
    echo [OK] Encontrado en: !SOURCE_DIR!
    goto :found_source
)

REM Opción 3: Buscar carpeta TECHCRM-POS en el directorio actual
if exist "%CURRENT_DIR%\TECHCRM-POS\TECHCRM-POS.exe" (
    set "SOURCE_DIR=%CURRENT_DIR%\TECHCRM-POS"
    echo [OK] Encontrado en: !SOURCE_DIR!
    goto :found_source
)

REM Si no se encuentra en ningún lugar
echo.
echo [ERROR] No se encontró TECHCRM-POS.exe
echo.
echo Se esperaba encontrar la carpeta TECHCRM-POS que contiene:
echo   - TECHCRM-POS.exe
echo   - _internal\ (carpeta con dependencias)
echo.
echo Ubicación del instalador: %~dp0
echo Ubicación actual: %CURRENT_DIR%
echo.
echo Por favor, asegúrese de que:
echo 1. Ha extraído correctamente el ZIP
echo 2. La carpeta TECHCRM-POS está presente
echo 3. Contiene el archivo TECHCRM-POS.exe
echo.
pause
exit /b 1

:found_source
echo.
echo Verificando estructura...
if not exist "!SOURCE_DIR!\TECHCRM-POS.exe" (
    echo [ERROR] No se encontró TECHCRM-POS.exe en !SOURCE_DIR!
    pause
    exit /b 1
)
if not exist "!SOURCE_DIR!\_internal" (
    echo [ERROR] No se encontró carpeta _internal en !SOURCE_DIR!
    pause
    exit /b 1
)
echo [OK] Estructura verificada correctamente
echo.

REM ============================================================
REM 3. DEFINIR RUTA DE INSTALACIÓN
REM ============================================================
set "INSTALL_DIR=C:\Program Files\TECHCRM POS"
echo [INFO] Ruta de instalación: %INSTALL_DIR%
echo.

REM ============================================================
REM 4. CREAR DIRECTORIO DE INSTALACIÓN
REM ============================================================
if not exist "%INSTALL_DIR%" (
    echo [INFO] Creando directorio de instalación...
    mkdir "%INSTALL_DIR%" >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el directorio: %INSTALL_DIR%
        echo Intente ejecutar el instalador como administrador.
        pause
        exit /b 1
    )
    echo [OK] Directorio creado
) else (
    echo [INFO] Directorio ya existe
)
echo.

REM ============================================================
REM 5. COPIAR ARCHIVOS
REM ============================================================
echo [INFO] Copiando archivos de aplicación...
echo.

REM Copiar archivo ejecutable
copy /Y "!SOURCE_DIR!\TECHCRM-POS.exe" "%INSTALL_DIR%\TECHCRM-POS.exe" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se pudo copiar TECHCRM-POS.exe
    pause
    exit /b 1
)
echo [OK] TECHCRM-POS.exe copiado

REM Copiar dependencias
xcopy /E /I /Y "!SOURCE_DIR!\_internal" "%INSTALL_DIR%\_internal" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se pudo copiar carpeta _internal
    pause
    exit /b 1
)
echo [OK] Dependencias copiadas (_internal)

REM Copiar carpeta data si existe
if exist "!SOURCE_DIR!\..\data" (
    xcopy /E /I /Y "!SOURCE_DIR!\..\data" "%INSTALL_DIR%\data" >nul 2>&1
    echo [OK] Datos copiados (data)
)

REM Copiar carpeta comprobantes si existe
if exist "!SOURCE_DIR!\..\comprobantes" (
    xcopy /E /I /Y "!SOURCE_DIR!\..\comprobantes" "%INSTALL_DIR%\comprobantes" >nul 2>&1
    echo [OK] Comprobantes copiados
)

echo.

REM ============================================================
REM 6. CREAR ACCESO DIRECTO EN EL ESCRITORIO
REM ============================================================
echo [INFO] Creando acceso directo en el escritorio...
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT=%DESKTOP%\TECHCRM POS.lnk"

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\TECHCRM-POS.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'TECHCRM POS - Sistema de Punto de Venta'; $Shortcut.Save()" >nul 2>&1
if errorlevel 1 (
    echo [AVISO] No se pudo crear acceso directo en el escritorio
) else (
    echo [OK] Acceso directo creado en: %DESKTOP%
)
echo.

REM ============================================================
REM 7. CREAR ACCESO DIRECTO EN MENÚ INICIO
REM ============================================================
echo [INFO] Creando acceso directo en el Menú Inicio...
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
set "START_SHORTCUT=%START_MENU%\TECHCRM POS.lnk"

if not exist "%START_MENU%" mkdir "%START_MENU%" >nul 2>&1

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_SHORTCUT%'); $Shortcut.TargetPath = '%INSTALL_DIR%\TECHCRM-POS.exe'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'TECHCRM POS - Sistema de Punto de Venta'; $Shortcut.Save()" >nul 2>&1
if errorlevel 1 (
    echo [AVISO] No se pudo crear acceso directo en el Menú Inicio
) else (
    echo [OK] Acceso directo creado en: Menú Inicio
)
echo.

REM ============================================================
REM 8. REGISTRAR EN EL REGISTRO DE WINDOWS (OPCIONAL)
REM ============================================================
echo [INFO] Registrando aplicación en Windows...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM-POS" /v "DisplayName" /d "TECHCRM POS v2.0" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM-POS" /v "InstallLocation" /d "%INSTALL_DIR%" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM-POS" /v "Version" /d "2.0" /f >nul 2>&1
echo [OK] Aplicación registrada en Windows
echo.

REM ============================================================
REM 9. CREAR SCRIPT DE DESINSTALACIÓN
REM ============================================================
set "UNINSTALL_BAT=%INSTALL_DIR%\Desinstalar.bat"
(
echo @echo off
echo title Desinstalador de TECHCRM POS
echo cls
echo echo.
echo echo ╔════════════════════════════════════════════════════════════╗
echo echo ║             DESINSTALACIÓN DE TECHCRM POS                  ║
echo echo ╚════════════════════════════════════════════════════════════╝
echo echo.
echo set /p confirm="¿Deseas desinstalar TECHCRM POS? [S/N]: "
echo if /i not "!confirm!"=="S" exit /b
echo.
echo echo Desinstalando...
echo taskkill /IM TECHCRM-POS.exe /F >nul 2>&1
echo timeout /t 2 >nul
echo.
echo rmdir /s /q "%INSTALL_DIR%" >nul 2>&1
echo del "%%DESKTOP%%\TECHCRM POS.lnk" >nul 2>&1
echo del "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\TECHCRM POS.lnk" >nul 2>&1
echo reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM-POS" /f >nul 2>&1
echo.
echo echo [OK] TECHCRM POS ha sido desinstalado correctamente
echo echo.
echo pause
) > "%UNINSTALL_BAT%"
echo [OK] Script de desinstalación creado: Desinstalar.bat
echo.

REM ============================================================
REM 10. FINALIZACIÓN
REM ============================================================
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║       ✓ INSTALACIÓN COMPLETADA CORRECTAMENTE              ║
echo ║                                                            ║
echo ║  TECHCRM POS v2.0 ha sido instalado en:                  ║
echo ║  %INSTALL_DIR%                           ║
echo ║                                                            ║
echo ║  Puedes acceder a través de:                             ║
echo ║  - Acceso directo en el Escritorio                       ║
echo ║  - Menú Inicio de Windows                                ║
echo ║  - %INSTALL_DIR%\TECHCRM-POS.exe          ║
echo ║                                                            ║
echo ║  Para desinstalar, ejecuta:                              ║
echo ║  %INSTALL_DIR%\Desinstalar.bat            ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo Presiona cualquier tecla para salir...
pause >nul
exit /b 0
