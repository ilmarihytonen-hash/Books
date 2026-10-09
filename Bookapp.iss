#define MyAppName "Bookapp"
#ifndef MyAppVersion
  #define MyAppVersion "0.2.0-beta.1"
#endif

[Setup]
AppId={{DF29AA41-7D04-41F4-BFF3-736255013E9A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Bookapp
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir=dist
OutputBaseFilename=Bookapp-Setup
UninstallDisplayIcon={app}\Bookapp.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\Bookapp.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Bookapp"; Filename: "{app}\Bookapp.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Bookapp"; Filename: "{app}\Bookapp.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Bookapp.exe"; Description: "Launch Bookapp"; Flags: postinstall nowait skipifsilent
