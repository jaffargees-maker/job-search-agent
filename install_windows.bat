@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   Job Search Agent - first-time setup
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found on this computer.
  echo.
  echo 1. Go to https://www.python.org/downloads/windows/
  echo 2. Download and run the Windows installer
  echo 3. IMPORTANT: check "Add python.exe to PATH" on the first screen
  echo 4. Once installed, close this window and double-click install_windows.bat again
  echo.
  pause
  exit /b 1
)

if not exist venv (
  echo Creating a virtual environment...
  python -m venv venv
) else (
  echo Virtual environment already exists, reusing it.
)

call venv\Scripts\activate.bat

echo.
echo Installing dependencies - this can take a few minutes the first time...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo.
echo Installing the browser used for filling out applications...
playwright install chromium

if not exist logs mkdir logs
if not exist applications mkdir applications
if not exist uploads mkdir uploads

echo.
echo ============================================
echo   Setup complete - starting the dashboard
echo ============================================
echo.
echo Opening http://127.0.0.1:5050 in your browser...
echo Leave this window open while you use the dashboard.
echo Close this window (or press Ctrl+C) to stop it.
echo.

start "" http://127.0.0.1:5050
python app.py

pause
