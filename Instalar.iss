; ============================================================
; TECHCRM POS - SCRIPT DE INSTALACIÓN INNO SETUP
; ============================================================
; Este script configura Inno Setup para crear un instalador
; profesional de TECHCRM POS para Windows.
;
; Uso:
;   iscc Instalar.iss
;
; Resultado:
;   Output\Instalar.exe (instalador ejecutable)
; ============================================================

[Setup]
; Información básica de la aplicación
AppName=TECHCRM POS
AppVersion=1.0.0
AppPublisher=TECHCRM Systems
AppPublisherURL=https://techcrm.local
AppSupportURL=https://techcrm.local/soporte
AppUpdatesURL=https://techcrm.local/actualizaciones
DefaultDirName={pf}\TECHCRM POS
DefaultGroupName=TECHCRM POS
OutputDir=Output
OutputBaseFilename=Instalar
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64

; Información de versión
VersionInfoVersion=1.0.0.0
VersionInfoCompany=TECHCRM Systems
VersionInfoDescription=Sistema POS para Comidas Rápidas
VersionInfoCopyright=© 2026 TECHCRM Systems
VersionInfoProductName=TECHCRM POS
VersionInfoProductVersion=1.0.0

; Configuración visual
WizardStyle=modern
SetupIconFile=app\assets\icon.ico
UninstallDisplayIcon={app}\TECHCRM-POS.exe
LicenseFile=LICENSE.txt
UninstallDisplayName=Desinstalar TECHCRM POS

; Configuración de permisos y privilegios
PrivilegesRequired=admin
AllowUNCPath=no
AlwaysShowDirOnReadyPage=yes
AlwaysShowGroupOnReadyPage=yes
AlwaysShowComponentsList=yes
ShowLanguageDialog=yes
LanguageDetectionMethod=uilanguage

; Registro en Windows
ChangesAssociations=yes
ChangesEnvironment=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Languages\English.isl"

[CustomMessages]
spanish.BtnNext=&Siguiente
spanish.BtnInstall=&Instalar
spanish.BtnFinish=&Finalizar
spanish.WelcomeLabel1=Bienvenido al Instalador de TECHCRM POS
spanish.WelcomeLabel2=Instalará TECHCRM POS v1.0.0 en su computadora.%n%nSe recomienda cerrar cualquier otra aplicación antes de continuar.

english.BtnNext=&Next
english.BtnInstall=&Install
english.BtnFinish=&Finish
english.WelcomeLabel1=Welcome to TECHCRM POS Installer
english.WelcomeLabel2=This will install TECHCRM POS v1.0.0 on your computer.%n%nIt is recommended to close all other applications before continuing.

[Types]
Name: "full"; Description: "Instalación Completa / Full Installation"; Flags: iscustom
Name: "compact"; Description: "Instalación Mínima / Minimal Installation"; Flags: iscustom
Name: "custom"; Description: "Instalación Personalizada / Custom Installation"; Flags: iscustom

[Components]
Name: "app"; Description: "Aplicación TECHCRM POS / TECHCRM POS Application"; Types: full compact custom; Flags: fixed
Name: "diagnostico"; Description: "Herramienta de Diagnóstico / Diagnostic Tool"; Types: full custom; Flags: checkablealone
Name: "accesos"; Description: "Crear Accesos Directos / Create Shortcuts"; Types: full custom; Flags: checkablealone

[Files]
; Aplicación principal
Source: "dist\TECHCRM-POS\*"; DestDir: "{app}"; Components: app; Flags: ignoreversion recursesubdirs createallsubdirs

; Herramienta de diagnóstico (opcional)
Source: "dist\TECHCRM-POS-Diagnostico\TECHCRM-POS-Diagnostico.exe"; DestDir: "{app}"; Components: diagnostico; Flags: ignoreversion

; Documentación y recursos
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\data"
Name: "{app}\comprobantes"
Name: "{app}\logs"

[Icons]
; Acceso directo en el escritorio
Name: "{userdesktop}\TECHCRM POS"; Filename: "{app}\TECHCRM-POS.exe"; Components: accesos; WorkingDir: "{app}"; IconFileName: "{app}\TECHCRM-POS.exe"; Comment: "Sistema POS para Comidas Rápidas"

; Acceso directo en el menú Inicio
Name: "{group}\TECHCRM POS"; Filename: "{app}\TECHCRM-POS.exe"; WorkingDir: "{app}"; IconFileName: "{app}\TECHCRM-POS.exe"; Comment: "Sistema POS para Comidas Rápidas"
Name: "{group}\Diagnóstico"; Filename: "{app}\TECHCRM-POS-Diagnostico.exe"; Components: diagnostico; WorkingDir: "{app}"; Comment: "Herramienta de Diagnóstico"
Name: "{group}\Desinstalar"; Filename: "{uninstallexe}"; Comment: "Desinstalar TECHCRM POS"

[Run]
; Ejecutar la aplicación después de la instalación (opcional)
Filename: "{app}\TECHCRM-POS.exe"; Description: "Ejecutar TECHCRM POS ahora / Run TECHCRM POS now"; Flags: nowait postinstall skipifsilent; Components: app

[UninstallDelete]
; Eliminar archivos y carpetas al desinstalar
Type: dirifempty; Name: "{app}\data"
Type: dirifempty; Name: "{app}\comprobantes"
Type: dirifempty; Name: "{app}\logs"
Type: dirifempty; Name: "{app}\app"
Type: dirifempty; Name: "{app}\_internal"
Type: dirifempty; Name: "{app}"

[Registry]
; Registrar aplicación en Windows para aparecer en "Agregar/Quitar Programas"
Root: "HKLM"; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS"; ValueType: string; ValueName: "DisplayName"; ValueData: "TECHCRM POS v1.0.0"; Flags: uninsdeletekey
Root: "HKLM"; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "1.0.0"
Root: "HKLM"; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS"; ValueType: string; ValueName: "Publisher"; ValueData: "TECHCRM Systems"
Root: "HKLM"; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"
Root: "HKLM"; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS"; ValueType: string; ValueName: "DisplayIcon"; ValueData: "{app}\TECHCRM-POS.exe,0"
Root: "HKLM"; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS"; ValueType: string; ValueName: "UninstallString"; ValueData: "{uninstallexe}"
Root: "HKLM"; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS"; ValueType: dword; ValueName: "NoModify"; ValueData: "1"
Root: "HKLM"; Subkey: "Software\Microsoft\Windows\CurrentVersion\Uninstall\TECHCRM POS"; ValueType: dword; ValueName: "NoRepair"; ValueData: "1"

[Code]
{ ============================================================
  FUNCIONES DE PERSONALIZACIÓN
  ============================================================ }

function InitializeSetup(): Boolean;
var
  ErrorCode: Integer;
begin
  Result := True;
  
  { Verificar que Windows 10 o superior está instalado }
  if WindowsVersion < wv10 then
  begin
    MsgBox('Windows 10 o superior es requerido.' + #13 + 'Windows 10 or later is required.', mbCriticalError, MB_OK);
    Result := False;
    Exit;
  end;
  
  { Mostrar mensaje de bienvenida }
  if GetUILanguage() = 0x0c0a then { Español }
    MsgBox('Este asistente instalará TECHCRM POS.' + #13 + #13 + 'Se requieren permisos de administrador.' + #13 + 'Se recomienda tener 500 MB de espacio libre.', mbInformation, MB_OK)
  else
    MsgBox('This wizard will install TECHCRM POS.' + #13 + #13 + 'Administrator privileges are required.' + #13 + 'At least 500 MB of free space is recommended.', mbInformation, MB_OK);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssFinished then
  begin
    { Mostrar mensaje final }
    if GetUILanguage() = 0x0c0a then { Español }
      MsgBox('TECHCRM POS se ha instalado correctamente.' + #13 + #13 + 'Podrás encontrarlo en el menú Inicio como "TECHCRM POS".' + #13 + 'También hay un acceso directo en el escritorio.', mbInformation, MB_OK)
    else
      MsgBox('TECHCRM POS has been installed successfully.' + #13 + #13 + 'You can find it in the Start menu as "TECHCRM POS".' + #13 + 'There is also a shortcut on your desktop.', mbInformation, MB_OK);
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
end;

