@echo off
REM ============================================================
REM INSTALADOR DE TCRM v1.0 - Sistema POS para Windows
REM ============================================================

setlocal enabledelayedexpansion

cls
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║                 INSTALADOR DE TCRM v1.0                       ║
echo ║              Sistema POS para Comidas Rápidas                 ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Verificar si se ejecuta como administrador
net session >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Este instalador requiere permisos de administrador.
    echo.
    echo Presiona cualquier tecla para reintentar como administrador...
    pause >nul
    
    REM Relanzar como administrador
    PowerShell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

echo ✓ Permisos de administrador confirmados
echo.

REM Obtener ruta de instalación
set "INSTALL_DIR=C:\Program Files\TCRM"

echo [1/5] Preparando instalación...
echo       Destino: %INSTALL_DIR%
echo.

REM Crear directorio si no existe
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo ✓ Carpeta de instalación creada
) else (
    echo ✓ Carpeta de instalación ya existe
)

REM Copiar archivos
echo.
echo [2/5] Copiando archivos...

REM Buscar TCRM.exe en ubicaciones posibles
set "EXE_SOURCE="
if exist "TCRM.exe" (
    set "EXE_SOURCE=TCRM.exe"
) else if exist "dist\TCRM\TCRM.exe" (
    set "EXE_SOURCE=dist\TCRM\TCRM.exe"
)

if "%EXE_SOURCE%"=="" (
    echo ✗ No se encontró TCRM.exe
    echo.
    echo   Buscamos en:
    echo   • TCRM.exe (raíz)
    echo   • dist\TCRM\TCRM.exe
    echo.
    echo   Verifica que hayas extraído correctamente el ZIP
    pause
    exit /b 1
)

copy /Y "%EXE_SOURCE%" "%INSTALL_DIR%\TCRM.exe" >nul 2>&1
if errorlevel 1 (
    echo ✗ Error al copiar TCRM.exe desde: %EXE_SOURCE%
    pause
    exit /b 1
)
echo ✓ Ejecutable copiado

if exist "app" (
    xcopy /E /I /Y "app" "%INSTALL_DIR%\app" >nul 2>&1
    echo ✓ Recursos copiados
) else (
    echo ⚠ Carpeta 'app' no encontrada (opcional)
)

if exist "requirements.txt" (
    copy /Y "requirements.txt" "%INSTALL_DIR%\requirements.txt" >nul 2>&1
    echo ✓ Dependencias copiadas
) else (
    echo ⚠ requirements.txt no encontrado (opcional)
)

REM Crear acceso directo en escritorio
echo.
echo [3/5] Creando accesos directos...

set "DESKTOP=%USERPROFILE%\Desktop"

REM Usar PowerShell para crear acceso directo
powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%DESKTOP%\TCRM.lnk'); " ^
    "$Shortcut.TargetPath = '%INSTALL_DIR%\TCRM.exe'; " ^
    "$Shortcut.WorkingDirectory = '%INSTALL_DIR%'; " ^
    "$Shortcut.IconLocation = '%INSTALL_DIR%\TCRM.exe'; " ^
    "$Shortcut.Save()"

echo ✓ Acceso directo en escritorio creado

REM Crear entrada en menú de inicio
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
mkdir "%START_MENU%\TCRM" 2>nul

powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%START_MENU%\TCRM\TCRM.lnk'); " ^
    "$Shortcut.TargetPath = '%INSTALL_DIR%\TCRM.exe'; " ^
    "$Shortcut.WorkingDirectory = '%INSTALL_DIR%'; " ^
    "$Shortcut.IconLocation = '%INSTALL_DIR%\TCRM.exe'; " ^
    "$Shortcut.Save()"

echo ✓ Entrada en menú de inicio creada

REM Crear desinstalador
echo.
echo [4/5] Creando desinstalador...

(
echo @echo off
echo REM Desinstalador de TCRM
echo set "INSTALL_DIR=C:\Program Files\TCRM"
echo.
echo cls
echo echo.
echo echo ⚠️  ¿Deseas desinstalar TCRM?
echo echo.
echo set /p CONFIRM="Escribe 'SI' para desinstalar: "
echo.
echo if /i not "!CONFIRM!"=="SI" (
echo     echo Desinstalación cancelada.
echo     pause
echo     exit /b
echo ^)
echo.
echo echo Eliminando archivos...
echo rmdir /s /q "%INSTALL_DIR%"
echo.
echo echo Eliminando accesos directos...
echo del /q "%USERPROFILE%\Desktop\TCRM.lnk" 2^>nul
echo del /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\TCRM\*" 2^>nul
echo rmdir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\TCRM" 2^>nul
echo.
echo echo Eliminando entrada del registro...
echo reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TCRM" /f 2^>nul
echo.
echo echo ✓ Desinstalación completada.
echo pause
) > "%INSTALL_DIR%\Desinstalar_TCRM.bat"

echo ✓ Desinstalador creado

REM Agregar al registro de Windows
echo.
echo [5/5] Registrando aplicación en Windows...

reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TCRM" /v "DisplayName" /d "TCRM - Sistema POS" /f >nul
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TCRM" /v "DisplayIcon" /d "%INSTALL_DIR%\TCRM.exe" /f >nul
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TCRM" /v "DisplayVersion" /d "1.0.0" /f >nul
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TCRM" /v "UninstallString" /d "%INSTALL_DIR%\Desinstalar_TCRM.bat" /f >nul
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TCRM" /v "Publisher" /d "TCRM Systems" /f >nul
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TCRM" /v "InstallLocation" /d "%INSTALL_DIR%" /f >nul

echo ✓ Aplicación registrada en Windows

REM Mostrar resumen
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║            ✅ ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!           ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 🎉 TCRM ha sido instalado correctamente como aplicación Windows
echo.
echo 📍 Ubicación: %INSTALL_DIR%
echo.
echo 🔑 Credenciales por defecto:
echo    Usuario: techcrm
echo    Contraseña: 1234567
echo.
echo ✨ Ahora puedes:
echo    • Buscar "TCRM" en el menú de inicio
echo    • Hacer clic en el acceso directo del escritorio
echo    • Desinstalar desde Panel de Control
echo.
echo 📚 Para desinstalar:
echo    Panel de Control → Programas → Desinstalar un programa
echo    O ejecuta: %INSTALL_DIR%\Desinstalar_TCRM.bat
echo.

REM Preguntar si desea iniciar TCRM ahora
echo.
set /p LAUNCH="¿Deseas abrir TCRM ahora? (S/N): "

if /i "%LAUNCH%"=="S" (
    echo.
    echo Iniciando TCRM...
    start "" "%INSTALL_DIR%\TCRM.exe"
) else (
    echo.
    echo Para iniciar TCRM en el futuro, busca "TCRM" en el menú de inicio.
)

echo.
pause
