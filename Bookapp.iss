#define MyAppName "Bookapp"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.9"
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
SetupIconFile=bookapplogo.ico
UninstallDisplayIcon={app}\Bookapp.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "dist\Bookapp.exe"; DestDir: "{app}"; Flags: ignoreversion; Permissions: users-full
Source: "bookapplogo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Bookapp"; Filename: "{app}\Bookapp.exe"; WorkingDir: "{app}"; IconFilename: "{app}\bookapplogo.ico"
Name: "{autodesktop}\Bookapp"; Filename: "{app}\Bookapp.exe"; WorkingDir: "{app}"; IconFilename: "{app}\bookapplogo.ico"; Tasks: desktopicon

[Dirs]
Name: "{app}"; Permissions: users-full

[Run]
Filename: "{app}\Bookapp.exe"; Description: "Launch Bookapp"; Flags: postinstall nowait skipifsilent
