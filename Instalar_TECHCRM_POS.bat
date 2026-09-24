@echo off
REM ============================================================
REM TECHCRM POS v1.0.0 - INSTALADOR WINDOWS
REM ============================================================
REM Instalador simple y funcional para TECHCRM POS
REM ============================================================

setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

cls

REM ============================================================
REM 1. VERIFICAR PERMISOS DE ADMINISTRADOR
REM ============================================================

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║                  TECHCRM POS - INSTALADOR v1.0                ║
echo ║              Sistema POS para Comidas Rápidas                 ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
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
REM 2. DEFINIR RUTAS
REM ============================================================

set "INSTALL_DIR=%ProgramFiles%\TECHCRM POS"
set "SOURCE_DIR=dist\TECHCRM-POS"

echo [INFO] Verificando estructura del proyecto...

if not exist "%SOURCE_DIR%\TECHCRM-POS.exe" (
    echo [ERROR] No se encontró TECHCRM-POS.exe
    echo Ubicación esperada: %cd%\%SOURCE_DIR%\TECHCRM-POS.exe
    echo.
    echo Asegúrate de ejecutar este instalador desde la raíz del proyecto.
    pause
    exit /b 1
)

echo [OK] Ejecutable encontrado
echo.

REM ============================================================
REM 3. CREAR DIRECTORIO DE INSTALACIÓN
REM ============================================================

echo [INFO] Creando directorio de instalación...

if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el directorio de instalación
        pause
        exit /b 1
    )
    echo [OK] Directorio creado: %INSTALL_DIR%
) else (
    echo [AVISO] El directorio ya existe. Se sobrescribirán archivos.
)

echo.

REM ============================================================
REM 4. COPIAR ARCHIVOS
REM ============================================================

echo [INFO] Copiando archivos...

REM Copiar todo el contenido de dist\TECHCRM-POS a Program Files
echo [INFO] Copiando TECHCRM-POS.exe...
copy /Y "%SOURCE_DIR%\TECHCRM-POS.exe" "%INSTALL_DIR%\TECHCRM-POS.exe" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se pudo copiar TECHCRM-POS.exe
    pause
    exit /b 1
)
echo [OK] TECHCRM-POS.exe copiado

REM Copiar carpeta _internal (muy importante)
echo [INFO] Copiando componentes internos (_internal)...
xcopy /E /I /Y "%SOURCE_DIR%\_internal" "%INSTALL_DIR%\_internal" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se pudo copiar los componentes internos
    pause
    exit /b 1
)
echo [OK] Componentes internos copiados

echo.

REM ============================================================
REM 5. CREAR ACCESO DIRECTO EN ESCRITORIO
REM ============================================================

echo [INFO] Creando acceso directo en escritorio...

set "DESKTOP=%USERPROFILE%\Desktop"

powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%DESKTOP%\TECHCRM POS.lnk'); " ^
    "$Shortcut.TargetPath = '%INSTALL_DIR%\TECHCRM-POS.exe'; " ^
    "$Shortcut.WorkingDirectory = '%INSTALL_DIR%'; " ^
    "$Shortcut.IconLocation = '%INSTALL_DIR%\TECHCRM-POS.exe'; " ^
    "$Shortcut.Description = 'Sistema POS para Comidas Rápidas'; " ^
    "$Shortcut.Save()"

if errorlevel 1 (
    echo [AVISO] No se pudo crear acceso directo en escritorio
) else (
    echo [OK] Acceso directo en escritorio creado
)

echo.

REM ============================================================
REM 6. CREAR ENTRADA EN MENÚ DE INICIO
REM ============================================================

echo [INFO] Agregando al menú de inicio...

set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\TECHCRM POS"

if not exist "%START_MENU%" mkdir "%START_MENU%"

powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%START_MENU%\TECHCRM POS.lnk'); " ^
    "$Shortcut.TargetPath = '%INSTALL_DIR%\TECHCRM-POS.exe'; " ^
    "$Shortcut.WorkingDirectory = '%INSTALL_DIR%'; " ^
    "$Shortcut.IconLocation = '%INSTALL_DIR%\TECHCRM-POS.exe'; " ^
    "$Shortcut.Description = 'Sistema POS para Comidas Rápidas'; " ^
    "$Shortcut.Save()"

if errorlevel 1 (
    echo [AVISO] No se pudo agregar al menú de inicio
) else (
    echo [OK] Entrada agregada al menú de inicio
)

echo.

REM ============================================================
REM 7. CREAR DESINSTALADOR
REM ============================================================

echo [INFO] Creando desinstalador...

(
echo @echo off
echo set "INSTALL_DIR=%INSTALL_DIR%"
echo.
echo cls
echo echo.
echo echo Desinstalador de TECHCRM POS
echo echo.
echo set /p CONFIRM="¿Deseas desinstalar TECHCRM POS? (SI/NO): "
echo.
echo if /i not "!CONFIRM!"=="SI" (
echo     echo Desinstalacion cancelada.
echo     pause
echo     exit /b
echo ^)
echo.
echo echo Eliminando archivos...
echo rmdir /s /q "!INSTALL_DIR!" 2^>nul
echo.
echo echo Eliminando accesos directos...
echo del /q "%%USERPROFILE%%\Desktop\TECHCRM POS.lnk" 2^>nul
echo del /q "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\TECHCRM POS\*" 2^>nul
echo rmdir "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\TECHCRM POS" 2^>nul
echo.
echo reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /f 2^>nul
echo.
echo echo Desinstalacion completada.
echo pause
) > "%INSTALL_DIR%\Desinstalar_TECHCRM.bat"

echo [OK] Desinstalador creado
echo.

REM ============================================================
REM 8. REGISTRAR EN WINDOWS
REM ============================================================

echo [INFO] Registrando en Windows...

reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /v "DisplayName" /d "TECHCRM POS - Sistema POS v1.0.0" /f >nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /v "DisplayIcon" /d "%INSTALL_DIR%\TECHCRM-POS.exe" /f >nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /v "DisplayVersion" /d "1.0.0" /f >nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /v "InstallLocation" /d "%INSTALL_DIR%" /f >nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /v "UninstallString" /d "%INSTALL_DIR%\Desinstalar_TECHCRM.bat" /f >nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /v "Publisher" /d "TECHCRM Systems" /f >nul 2>&1

if errorlevel 1 (
    echo [AVISO] No se pudo registrar completamente en Windows
) else (
    echo [OK] Aplicacion registrada en Windows
)

echo.

REM ============================================================
REM 9. MENSAJE FINAL
REM ============================================================

cls

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║         OK INSTALACION COMPLETADA EXITOSAMENTE                ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo TECHCRM POS v1.0.0 se ha instalado correctamente
echo.
echo Ubicacion: %INSTALL_DIR%
echo.
echo Credenciales por defecto:
echo   Usuario:      techcrm
echo   Contraseña:   1234567
echo.
echo IMPORTANTE: Cambia la contraseña en tu primer acceso
echo             (Configuracion → Identidad → Admin)
echo.
echo Ahora puedes:
echo   • Buscar "TECHCRM POS" en el menu de inicio
echo   • Usar el acceso directo del escritorio
echo   • Desinstalar desde Panel de Control
echo.
echo ════════════════════════════════════════════════════════════════
echo.

set /p LAUNCH="¿Deseas ejecutar TECHCRM POS ahora? (S/N): "

if /i "%LAUNCH%"=="S" (
    echo.
    echo Iniciando TECHCRM POS...
    start "" "%INSTALL_DIR%\TECHCRM-POS.exe"
) else (
    echo.
    echo Para iniciar TECHCRM POS en el futuro:
    echo   • Busca en el menu de inicio
    echo   • O usa el acceso directo del escritorio
)

echo.
pause

endlocal
