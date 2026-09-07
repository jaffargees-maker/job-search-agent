@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   Job Search Agent - build installer
echo ============================================
echo.
echo This is a ONE-TIME step for whoever is packaging the app (you), not
echo something each applicant needs to run. It produces JobSearchAgentSetup.exe
echo in the Output folder - THAT is the file to hand out. Applicants just
echo double-click it; they never see this window.
echo.
echo Must be run on Windows (PyInstaller does not cross-compile from other
echo operating systems).
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install it from:
  echo   https://www.python.org/downloads/windows/
  echo ^(check "Add python.exe to PATH" during setup^), then run this again.
  pause
  exit /b 1
)

if not exist build_venv (
  echo Creating a build environment...
  python -m venv build_venv
)
call build_venv\Scripts\activate.bat

echo.
echo Installing build dependencies...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet pyinstaller

echo.
echo Downloading the Chromium browser component ^(bundled into no exe -
echo it installs itself on first run instead, to keep the exe small^)...
playwright install chromium

echo.
echo Building JobSearchAgent.exe with PyInstaller...
pyinstaller --noconfirm --clean job_agent.spec
if errorlevel 1 (
  echo.
  echo PyInstaller build failed - see the errors above.
  pause
  exit /b 1
)
echo.
echo   -^> dist\JobSearchAgent.exe built successfully.

echo.
echo Looking for Inno Setup ^(to build the one-click installer^)...
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
where ISCC.exe >nul 2>nul && set "ISCC=ISCC.exe"

if defined ISCC (
  "%ISCC%" installer.iss
  echo.
  echo ============================================
  echo   Done: Output\JobSearchAgentSetup.exe
  echo ============================================
  echo Hand THAT single file to applicants. They double-click it, it
  echo installs everything with no admin rights needed, and launches the
  echo dashboard automatically.
) else (
  echo.
  echo Inno Setup wasn't found, so the one-click installer wasn't built.
  echo Download it free from https://jrsoftware.org/isinfo.php, then either:
  echo   - run this script again, or
  echo   - open installer.iss in the Inno Setup app and click Compile.
  echo.
  echo In the meantime, dist\JobSearchAgent.exe already works as a standalone
  echo portable app: applicants can copy that one file anywhere and double-
  echo click it directly ^(it creates its own uploads\applications\logs
  echo folders next to itself the first time it runs^).
)

echo.
pause
