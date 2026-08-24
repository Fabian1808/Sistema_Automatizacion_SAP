; Inno Setup Script para SapDocumentAutomation
; Rutas relativas a ESTE archivo (installer\): el exe queda en ..\installer_output

#define AppName "SAP Document Automation"
#define AppVersion "1.0.0"
#define AppPublisher "Fabian1808"
#define AppExeName "SapDocumentAutomation.exe"

[Setup]
AppId={{8E7C4B2A-3D1F-4E9A-B5C8-9F2D6A1B3C7E}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\SapDocumentAutomation
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\installer_output
OutputBaseFilename=SapDocumentAutomation-Setup-{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\installer_output\SapDocumentAutomation.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\config\sap_selectors.yaml"; DestDir: "{app}\config"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; No borra datos de usuario (%APPDATA%\SAPDocumentAutomation)
Type: filesandordirs; Name: "{app}"