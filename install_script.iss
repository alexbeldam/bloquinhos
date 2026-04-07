#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif

[Setup]
AppName=Bloquinhos
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\Bloquinhos
DefaultGroupName=Bloquinhos
OutputDir=output
OutputBaseFilename=BloquinhosSetup
SetupIconFile=assets\img\icon.ico
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\bloquinhos\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Bloquinhos"; Filename: "{app}\bloquinhos.exe"
Name: "{autodesktop}\Bloquinhos"; Filename: "{app}\bloquinhos.exe"
