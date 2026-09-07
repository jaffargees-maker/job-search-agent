@echo off
setlocal
cd /d "%~dp0"

if not exist venv (
  echo Virtual environment not found - run install_windows.bat first.
  pause
  exit /b 1
)

call venv\Scripts\activate.bat
start "" http://127.0.0.1:5050
python app.py
pause
