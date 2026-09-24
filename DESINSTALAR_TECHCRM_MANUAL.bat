@echo off
echo ========================================
echo   DESINSTALADOR MANUAL TECHCRM
echo ========================================
echo.

REM Matar proceso si est? corriendo
taskkill /f /im TECHCRM.exe >nul 2>&1

REM Eliminar carpeta de instalaci?n
echo Eliminando archivos de programa...
if exist "C:\TECHCRM" (
    rmdir /s /q "C:\TECHCRM"
    echo - C:\TECHCRM eliminado
)

if exist "C:\Program Files\TECHCRM" (
    rmdir /s /q "C:\Program Files\TECHCRM"
    echo - C:\Program Files\TECHCRM eliminado
)

REM Eliminar datos (opcional - comentado por seguridad)
REM if exist "%LOCALAPPDATA%\TECHCRM" (
REM     rmdir /s /q "%LOCALAPPDATA%\TECHCRM"
REM     echo - Datos de usuario eliminados
REM )

REM Eliminar accesos directos
echo Eliminando accesos directos...
del /f /q "%PUBLIC%\Desktop\TECHCRM.lnk" >nul 2>&1
del /f /q "%USERPROFILE%\Desktop\TECHCRM.lnk" >nul 2>&1
del /f /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\TECHCRM.lnk" >nul 2>&1

REM Eliminar registro
echo Limpiando registro de Windows...
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM" /f >nul 2>&1

echo.
echo ========================================
echo   DESINSTALACION COMPLETADA
echo ========================================
echo.
echo TECHCRM ha sido desinstalado.
echo Los datos de usuario se mantuvieron en: %LOCALAPPDATA%\TECHCRM
echo (Elimina esa carpeta manualmente si deseas borrar todo)
echo.
pause
