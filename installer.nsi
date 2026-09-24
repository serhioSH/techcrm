; ============================================================
; TECHCRM POS - Instalador NSIS
; Compatible con Windows 10 y 11
; ============================================================

!define APPNAME "TECHCRM POS"
!define COMPANYNAME "TechPixel"
!define DESCRIPTION "Sistema de Punto de Venta para Restaurantes"
!define VERSIONMAJOR 3
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define HELPURL "https://github.com/techpixel/crm"
!define INSTALLSIZE 200000

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES64\${APPNAME}"

Name "${APPNAME}"
Icon "app\assets\icon.ico"
OutFile "TECHCRM-POS-Setup-v3.0.exe"

Page directory
Page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin"
    messageBox mb_iconstop "Se requieren privilegios de administrador!"
    setErrorLevel 740
    quit
${EndIf}
!macroend

Function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
FunctionEnd

Section "install"
    SetOutPath $INSTDIR
    
    ; Copiar todos los archivos
    File /r "dist\TECHCRM-POS\*.*"
    
    ; Crear acceso directo en escritorio
    CreateShortcut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\TECHCRM-POS.exe" "" "$INSTDIR\TECHCRM-POS.exe"
    
    ; Crear acceso directo en menú inicio
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\TECHCRM-POS.exe" "" "$INSTDIR\TECHCRM-POS.exe"
    CreateShortcut "$SMPROGRAMS\${APPNAME}\Desinstalar.lnk" "$INSTDIR\uninstall.exe"
    
    ; Información del desinstalador
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Agregar a Programas y Características
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\TECHCRM-POS.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
    
    MessageBox MB_OK "Instalación completada exitosamente!$\n$\nEncontrarás TECHCRM POS en tu escritorio."
SectionEnd

Section "Uninstall"
    ; Eliminar archivos
    RMDir /r "$INSTDIR"
    
    ; Eliminar accesos directos
    Delete "$DESKTOP\${APPNAME}.lnk"
    RMDir /r "$SMPROGRAMS\${APPNAME}"
    
    ; Eliminar del registro
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    
    MessageBox MB_OK "Desinstalación completada."
SectionEnd
