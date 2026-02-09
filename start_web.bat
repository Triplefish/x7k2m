@echo off
echo Starting Fund Tracker Web Interface...

REM Check if requirements are installed
pip install -r requirements.txt > nul 2>&1

REM Start the server in background and wait a bit
start /B python app.py

REM Wait for server to start (simple timeout)
timeout /t 3 /nobreak > nul

REM Open the browser
start http://127.0.0.1:8888

echo Server is running. Close this window to stop.
pause
