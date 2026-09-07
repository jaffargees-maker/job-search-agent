; Inno Setup script for Job Search Agent.
; Produces a single JobSearchAgentSetup.exe that an applicant can double-click
; to install everything, with no Python and no manual setup steps.
;
; Requires Inno Setup (free): https://jrsoftware.org/isinfo.php
; Build with the ISCC.exe compiler, or open this file in the Inno Setup IDE
; and click Compile. BUILD_INSTALLER.bat does this automatically if it finds
; Inno Setup installed.
;
; NOTE: dist\JobSearchAgent.exe must already exist (built by PyInstaller
; via job_agent.spec) before compiling this script.

#define MyAppName "Job Search Agent"
#define MyAppVersion "1.0"
#define MyAppExeName "JobSearchAgent.exe"

[Setup]
AppId={{B6E6F1D2-6E8B-4C6B-9B4E-9F0F6E1B6A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
; Per-user install under %LOCALAPPDATA% — no admin rights / UAC prompt
; needed, and the app can write its own data (config, resume, reports)
; right next to itself.
DefaultDirName={localappdata}\JobSearchAgent
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
OutputBaseFilename=JobSearchAgentSetup
OutputDir=Output
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "dist\JobSearchAgent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\uploads"
Name: "{app}\applications"
Name: "{app}\logs"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} now"; Flags: postinstall nowait skipifsilent
