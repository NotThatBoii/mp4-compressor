; Compile from the repository root with scripts/build-installer.ps1.
#ifndef MyAppVersion
  #error MyAppVersion must be supplied by the build script
#endif
#define AppRoot SourcePath + "..\dist\Compressly"

[Setup]
AppId={{CF56931D-AB1A-4600-9A60-E42873E91398}
AppName=Compressly
AppVersion={#MyAppVersion}
AppPublisher=NotThatBoii
AppPublisherURL=https://github.com/NotThatBoii
AppCopyright=Copyright (c) 2026 NotThatBoii
AppSupportURL=https://github.com/NotThatBoii/mp4-compressor/issues
AppUpdatesURL=https://github.com/NotThatBoii/mp4-compressor/releases
DefaultDirName={localappdata}\Programs\Compressly
DefaultGroupName=Compressly
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0.17763
OutputDir=..\dist\installer
OutputBaseFilename=Compressly-{#MyAppVersion}-Setup-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableWelcomePage=no
LicenseFile=..\LICENSE
UninstallDisplayIcon={app}\Compressly.exe
CloseApplications=no
RestartApplications=no
SetupLogging=yes
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany=NotThatBoii
VersionInfoDescription=Compressly Setup by NotThatBoii
InfoBeforeFile=install-info.txt

[Messages]
SetupWindowTitle=Compressly by NotThatBoii
WelcomeLabel1=Welcome to Compressly
WelcomeLabel2=Created by NotThatBoii%nhttps://github.com/NotThatBoii%n%nThis wizard will install Compressly on your computer.%n%nCompressly's original code is licensed under the MIT License. Bundled components retain their own licenses.

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Files]
Source: "{#AppRoot}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Compressly"; Filename: "{app}\Compressly.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Compressly"; Filename: "{app}\Compressly.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\Compressly.exe"; Description: "Launch Compressly"; Flags: nowait postinstall skipifsilent

; No broad UninstallDelete rules: user-created videos and application logs are
; never recursively removed. Inno tracks and removes only installed files.
