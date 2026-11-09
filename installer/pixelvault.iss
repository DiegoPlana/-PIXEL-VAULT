#define MyAppName "PIXEL VAULT"
#define MyAppVersion "0.2.0"
#define MyAppExeName "PixelVault.exe"

[Setup]
AppId={{FBD664B8-C02A-454E-BE5D-C3C14FE31862}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=PIXEL VAULT
DefaultDirName={autopf}\PIXEL VAULT
DefaultGroupName=PIXEL VAULT
OutputDir=..\release
OutputBaseFilename=PIXEL-VAULT-Setup-{#MyAppVersion}
SetupIconFile=..\assets\pixelvault.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Files]
Source: "..\dist\PixelVault.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\PIXEL VAULT"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\PIXEL VAULT"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir PIXEL VAULT"; Flags: nowait postinstall skipifsilent
