; TCRM Installer Script (NSIS)
; ============================================================
; Sistema POS - Instalador Windows

!include "MUI2.nsh"

; Configuración básica
Name "TCRM - Sistema POS"
OutFile "TCRM_Setup.exe"
InstallDir "$PROGRAMFILES\TCRM"
InstallDirRegKey HKLM "Software\TCRM" "Install_Dir"

; Solicitar permisos de administrador
RequestExecutionLevel admin

; Variables
Var StartMenuFolder

; Interfaz
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_STARTMENU "TCRM" $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "Spanish"

; Instalación
Section "Instalar TCRM"
  SetOutPath "$INSTDIR"
  
  ; Copiar archivos compilados
  File /r "dist\TCRM\*.*"
  
  ; Crear menú de inicio
  !insertmacro MUI_STARTMENU_WRITE_BEGIN "TCRM"
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\TCRM.lnk" "$INSTDIR\TCRM.exe"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Desinstalar TCRM.lnk" "$INSTDIR\Uninstall.exe"
  !insertmacro MUI_STARTMENU_WRITE_END
  
  ; Crear acceso directo en escritorio (opcional)
  CreateShortcut "$DESKTOP\TCRM.lnk" "$INSTDIR\TCRM.exe"
  
  ; Guardar información de desinstalación
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TCRM" "DisplayName" "TCRM - Sistema POS"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TCRM" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TCRM" "DisplayIcon" "$INSTDIR\TCRM.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TCRM" "DisplayVersion" "1.0.0"
  
  ; Crear desinstalador
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

; Desinstalación
Section "Uninstall"
  ; Eliminar acceso directo del escritorio
  Delete "$DESKTOP\TCRM.lnk"
  
  ; Eliminar accesos directos del menú de inicio
  !insertmacro MUI_STARTMENU_GETFOLDER "TCRM" $StartMenuFolder
  Delete "$SMPROGRAMS\$StartMenuFolder\TCRM.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Desinstalar TCRM.lnk"
  RMDir "$SMPROGRAMS\$StartMenuFolder"
  
  ; Eliminar archivos instalados
  RMDir /r "$INSTDIR"
  
  ; Eliminar registro
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TCRM"
  DeleteRegKey HKLM "Software\TCRM"
SectionEnd
