; Instalador de Windows (Inno Setup), copia del de Partes de salida. Lo compila la CI (compilar.yml), nunca en local.
; AppId propio y FIJO: con él, cada versión nueva sustituye a la anterior. No se cambia nunca.
#define MyAppName "Programaciones"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppPublisher "Carlos Ferrero Bonet"
#define MyAppExeName "Programaciones.exe"

[Setup]
AppId={{9F472F08-FCFE-4DD9-8668-F4CC256B9E6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Programaciones
DefaultGroupName=Programaciones
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
OutputDir=Output
OutputBaseFilename=Programaciones-{#MyAppVersion}-Windows-Setup
ArchitecturesInstallIn64BitMode=x64compatible
; Sin exigir administrador: en el centro casi nadie lo es (BLD-006 de Guardias).
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=yes
CloseApplicationsFilter=*.exe,*.dll,*.pyd
RestartApplications=no
SetupIconFile=imagenes\icono.ico

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "dist\Programaciones\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Programaciones"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Programaciones"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir Programaciones"; Flags: nowait postinstall skipifsilent

[Code]
{ Los ajustes viven en %APPDATA%\Programaciones, fuera del programa, y desinstalar no los toca. Las programaciones
  del profesor están donde él las guarda (y dentro de cada Word exportado). }

function DesinstaladorAnterior(): String;
var
  Clave: String;
  Valor: String;
begin
  Result := '';
  Clave := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\' +
           ExpandConstant('{#SetupSetting("AppId")}') + '_is1';
  if RegQueryStringValue(HKCU, Clave, 'UninstallString', Valor) then
    Result := Valor
  else if RegQueryStringValue(HKLM, Clave, 'UninstallString', Valor) then
    Result := Valor;
  Result := RemoveQuotes(Result);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Desinstalador: String;
  Codigo: Integer;
  Espera: Integer;
begin
  Result := '';
  Desinstalador := DesinstaladorAnterior();
  if (Desinstalador = '') or (not FileExists(Desinstalador)) then
    exit;
  if not Exec(Desinstalador, '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART', '',
              SW_HIDE, ewWaitUntilTerminated, Codigo) then
    exit;
  Espera := 0;
  while FileExists(Desinstalador) and (Espera < 60) do
  begin
    Sleep(500);
    Espera := Espera + 1;
  end;
end;
