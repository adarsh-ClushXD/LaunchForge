; Inno Setup Script for LaunchForge
; Requires PyInstaller output to be in dist\LaunchForge\

#define MyAppName "LaunchForge"
#define MyAppVersion "1.0.2"
#define MyAppPublisher "YourName"
#define MyAppExeName "LaunchForge.exe"
#define MyIcon "assets\icons\app.ico"

[Setup]
; App Information
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
VersionInfoVersion={#MyAppVersion}

; Output Configuration
OutputDir=dist
OutputBaseFilename=LaunchForge_Setup
SetupIconFile={#MyIcon}
Compression=lzma2/ultra64
SolidCompression=yes

; Privileges
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy all files and folders from the PyInstaller output
Source: "dist\LaunchForge\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; We also want to include the assets folder if not already bundled properly
; Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu Icon
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icons\app.ico"
; Desktop Icon
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icons\app.ico"; Tasks: desktopicon

[Run]
; Option to run after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
