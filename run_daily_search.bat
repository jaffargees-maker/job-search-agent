@echo off
cd /d "%~dp0"
if not exist logs mkdir logs
"%~dp0venv\Scripts\python.exe" main.py >> logs\cron.log 2>&1
