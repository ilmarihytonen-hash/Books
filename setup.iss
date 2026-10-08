#define AppVersion "1.0.3"

[Setup]
AppId={{CB1D5C67-73CF-4B4E-A020-4E974F5A4E2B}
AppName=Bookapp
AppVersion={#AppVersion}
AppPublisher=Bookapp
DefaultDirName={localappdata}\Programs\Bookapp
DefaultGroupName=Bookapp
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=Bookapp-Setup
UninstallDisplayIcon={app}\Bookapp.exe
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "dist\Bookapp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall
Source: "urls.yaml"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{autoprograms}\Bookapp"; Filename: "{app}\Bookapp.exe"
Name: "{autodesktop}\Bookapp"; Filename: "{app}\Bookapp.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Bookapp.exe"; Description: "Launch Bookapp"; Flags: postinstall nowait skipifsilent
