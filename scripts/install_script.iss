#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif

#ifndef MyAppName
  #define MyAppName "Bloquinhos"
#endif

#ifndef MyAppId
  #define MyAppId "bloquinhos"
#endif

#ifndef MyAppExe
  #define MyAppExe "bloquinhos.exe"
#endif

#ifndef MyOutputBaseFilename
  #define MyOutputBaseFilename "BloquinhosSetup"
#endif

#ifndef MyVersionInfoVersion
  #define MyVersionInfoVersion "0.0.0.0"
#endif

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
VersionInfoVersion={#MyVersionInfoVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=../output
OutputBaseFilename={#MyOutputBaseFilename}
SetupIconFile=../assets\img\icon.ico
Compression=lzma
SolidCompression=yes

[Files]
Source: "../dist\{#MyAppId}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "../assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
