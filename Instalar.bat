@echo off
REM ============================================================
REM TECHCRM POS - INSTALADOR DE WINDOWS
REM ============================================================
REM Este script instala TECHCRM POS como aplicación Windows.
REM
REM Requisitos:
REM   • Windows 10 o superior
REM   • Permisos de administrador
REM   • 500 MB de espacio libre
REM
REM Uso:
REM   1. Hacer doble clic en Instalar.bat
REM   2. Hacer clic en "SÍ" cuando se pida permisos de admin
REM   3. Seguir las instrucciones en pantalla
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
echo ║                  TECHCRM POS - INSTALADOR                     ║
echo ║               Sistema POS para Comidas Rápidas                ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

net session >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Este instalador requiere permisos de administrador.
    echo.
    echo Presiona cualquier tecla para reintentar con permisos elevados...
    pause >nul
    
    REM Relanzar como administrador
    PowerShell -Command "Start-Process '%~f0' -Verb runAs"
    exit /b
)

echo [OK] Permisos de administrador confirmados
echo.

REM ============================================================
REM 2. DETECTAR SISTEMA OPERATIVO
REM ============================================================

echo [INFO] Detectando sistema operativo...

for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j

if %VERSION% geq 10.0 (
    echo [OK] Windows 10 o superior detectado
) else (
    echo [ERROR] Windows 10 o superior es requerido
    echo Se detectó: Windows %VERSION%
    pause
    exit /b 1
)

echo.

REM ============================================================
REM 3. VERIFICAR ESTRUCTURA DEL INSTALADOR
REM ============================================================

echo [INFO] Verificando estructura del instalador...
echo.

if not exist "dist\TECHCRM-POS\TECHCRM-POS.exe" (
    echo [ERROR] TECHCRM-POS.exe no encontrado
    echo Ubicación esperada: dist\TECHCRM-POS\TECHCRM-POS.exe
    echo.
    echo Asegúrate de:
    echo   1. Extraer correctamente el archivo ZIP
    echo   2. No mover ni eliminar archivos
    echo   3. Tener todos los archivos del instalador
    pause
    exit /b 1
)

echo [OK] Ejecutable principal encontrado

if not exist "dist\TECHCRM-POS\_internal" (
    echo [ERROR] Archivos internos no encontrados
    pause
    exit /b 1
)

echo [OK] Estructura de archivos verificada
echo.

REM ============================================================
REM 4. DEFINIR DIRECTORIO DE INSTALACIÓN
REM ============================================================

echo [INFO] Configurando ubicación de instalación...

set "INSTALL_DIR=%ProgramFiles%\TECHCRM POS"

echo [OK] Ubicación: %INSTALL_DIR%
echo.

REM ============================================================
REM 5. CREAR DIRECTORIO DE INSTALACIÓN
REM ============================================================

echo [INFO] Creando directorio de instalación...

if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el directorio
        pause
        exit /b 1
    )
    echo [OK] Directorio creado
) else (
    echo [AVISO] Directorio ya existe
    echo        Se sobrescribirán archivos existentes
)

echo.

REM ============================================================
REM 6. COPIAR ARCHIVOS
REM ============================================================

echo [1/5] Copiando archivos...
echo.

REM Copiar ejecutable
copy /Y "dist\TECHCRM-POS\TECHCRM-POS.exe" "%INSTALL_DIR%\TECHCRM-POS.exe" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se pudo copiar TECHCRM-POS.exe
    pause
    exit /b 1
)
echo [OK] Ejecutable principal copiado

REM Copiar carpeta _internal
xcopy /E /I /Y "dist\TECHCRM-POS\_internal" "%INSTALL_DIR%\_internal" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se pudo copiar archivos internos
    pause
    exit /b 1
)
echo [OK] Archivos internos copiados

REM Copiar documentación (si existe)
if exist "README.md" copy /Y "README.md" "%INSTALL_DIR%\README.md" >nul 2>&1

echo.

REM ============================================================
REM 7. CREAR ACCESO DIRECTO EN ESCRITORIO
REM ============================================================

echo [2/5] Creando acceso directo en escritorio...

set "DESKTOP=%USERPROFILE%\Desktop"

REM Usar PowerShell para crear acceso directo (más confiable)
powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%DESKTOP%\TECHCRM POS.lnk'); " ^
    "$Shortcut.TargetPath = '%INSTALL_DIR%\TECHCRM-POS.exe'; " ^
    "$Shortcut.WorkingDirectory = '%INSTALL_DIR%'; " ^
    "$Shortcut.IconLocation = '%INSTALL_DIR%\TECHCRM-POS.exe'; " ^
    "$Shortcut.Save()"

if errorlevel 1 (
    echo [AVISO] No se pudo crear acceso directo en escritorio
) else (
    echo [OK] Acceso directo en escritorio creado
)

echo.

REM ============================================================
REM 8. CREAR ENTRADA EN MENÚ DE INICIO
REM ============================================================

echo [3/5] Agregando al menú de inicio...

set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\TECHCRM POS"

if not exist "%START_MENU%" mkdir "%START_MENU%"

powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%START_MENU%\TECHCRM POS.lnk'); " ^
    "$Shortcut.TargetPath = '%INSTALL_DIR%\TECHCRM-POS.exe'; " ^
    "$Shortcut.WorkingDirectory = '%INSTALL_DIR%'; " ^
    "$Shortcut.IconLocation = '%INSTALL_DIR%\TECHCRM-POS.exe'; " ^
    "$Shortcut.Save()"

if errorlevel 1 (
    echo [AVISO] No se pudo crear entrada en menú de inicio
) else (
    echo [OK] Entrada agregada al menú de inicio
)

echo.

REM ============================================================
REM 9. CREAR DESINSTALADOR
REM ============================================================

echo [4/5] Creando desinstalador...

(
echo @echo off
echo REM Desinstalador de TECHCRM POS
echo set "INSTALL_DIR=%INSTALL_DIR%"
echo.
echo cls
echo echo.
echo echo ⚠️  ¿DESEAS DESINSTALAR TECHCRM POS?
echo echo.
echo set /p CONFIRM="Escribe 'SI' para desinstalar: "
echo.
echo if /i not "!CONFIRM!"=="SI" (
echo     echo Desinstalación cancelada.
echo     pause
echo     exit /b
echo ^)
echo.
echo echo [INFO] Eliminando archivos...
echo rmdir /s /q "!INSTALL_DIR!" >nul 2>&1
echo.
echo echo [OK] Archivos eliminados
echo.
echo echo [INFO] Eliminando accesos directos...
echo del /q "%%USERPROFILE%%\Desktop\TECHCRM POS.lnk" 2^>nul
echo del /q "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\TECHCRM POS\*" 2^>nul
echo rmdir "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\TECHCRM POS" 2^>nul
echo.
echo echo [OK] Accesos directos eliminados
echo.
echo echo [INFO] Eliminando entrada del registro...
echo reg delete "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /f 2^>nul
echo.
echo echo [OK] Entrada del registro eliminada
echo.
echo echo ✓ DESINSTALACIÓN COMPLETADA
echo echo.
echo pause
) > "%INSTALL_DIR%\Desinstalar_TECHCRM.bat"

echo [OK] Desinstalador creado

echo.

REM ============================================================
REM 10. REGISTRAR EN WINDOWS
REM ============================================================

echo [5/5] Registrando aplicación en Windows...

reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /v "DisplayName" /d "TECHCRM POS - Sistema POS" /f >nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /v "DisplayIcon" /d "%INSTALL_DIR%\TECHCRM-POS.exe" /f >nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /v "DisplayVersion" /d "1.0.0" /f >nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /v "UninstallString" /d "%INSTALL_DIR%\Desinstalar_TECHCRM.bat" /f >nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /v "Publisher" /d "TECHCRM Systems" /f >nul 2>&1
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS" /v "InstallLocation" /d "%INSTALL_DIR%" /f >nul 2>&1

if errorlevel 1 (
    echo [AVISO] No se pudo registrar completamente en Windows
) else (
    echo [OK] Aplicación registrada en Windows
)

echo.

REM ============================================================
REM 11. MENSAJE FINAL
REM ============================================================

cls

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                                                                ║
echo ║         ✅  ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!             ║
echo ║                                                                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 🎉 TECHCRM POS se ha instalado correctamente
echo.
echo 📍 Ubicación: %INSTALL_DIR%
echo.
echo 🔑 Credenciales por defecto:
echo    Usuario:     techcrm
echo    Contraseña:  1234567
echo.
echo    ⚠️  IMPORTANTE: Cambia la contraseña después del primer acceso
echo    (Configuración → Identidad → Admin)
echo.
echo ✨ Ahora puedes:
echo    • Buscar "TECHCRM POS" en el menú de inicio
echo    • Hacer clic en el acceso directo del escritorio
echo    • Desinstalar desde Panel de Control
echo.
echo 📚 Para desinstalar:
echo    Panel de Control → Programas → Desinstalar un programa
echo    Busca "TECHCRM POS - Sistema POS" y haz clic en "Desinstalar"
echo.
echo    O ejecuta: %INSTALL_DIR%\Desinstalar_TECHCRM.bat
echo.
echo ════════════════════════════════════════════════════════════════
echo.

REM Preguntar si ejecutar la aplicación
set /p LAUNCH="¿Deseas ejecutar TECHCRM POS ahora? (S/N): "

if /i "%LAUNCH%"=="S" (
    echo.
    echo Iniciando TECHCRM POS...
    start "" "%INSTALL_DIR%\TECHCRM-POS.exe"
) else (
    echo.
    echo Para iniciar TECHCRM POS en el futuro:
    echo   • Busca "TECHCRM POS" en el menú de inicio
    echo   • O haz doble clic en el acceso directo del escritorio
)

echo.
pause

endlocal
