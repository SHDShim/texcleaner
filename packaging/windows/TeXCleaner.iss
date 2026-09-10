; TeXCleaner per-user installer. The build helper supplies MyAppVersion.

#define MyAppName "TeXCleaner"
#ifndef MyAppVersion
#define MyAppVersion "0.8.0"
#endif
#define MyAppPublisher "Dan Shim"
#define MyAppURL "https://github.com/shdshim/texcleaner"
#define MyAppExeName "TeXCleaner.exe"

[Setup]
AppId={{B6AD2B4B-50D4-4EDC-8C69-9B6DB6B8A5A2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\..\dist\installer
OutputBaseFilename=TeXCleaner-{#MyAppVersion}-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\..\texcleaner\assets\icons\texcleaner.ico
LicenseFile=..\..\LICENSE
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} installer
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "..\..\dist\TeXCleaner\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
