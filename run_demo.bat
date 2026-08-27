@echo off
echo ===================================================
echo   [Drone AI] Auto Demo Runner
echo ===================================================
echo.
echo 1. Starting GCS Server...
start "GCS Server" cmd /k "cd /d "%~dp0" && python gcs\app.py"

echo 2. Waiting for GCS Server (3 sec)...
timeout /t 3 > nul

echo 3. Opening Dashboard...
start http://127.0.0.1:5001

echo 4. Auto-loading Blackbox data... (Skipped for Live Mapping Demo)
timeout /t 2 > nul
:: curl -s -X POST http://127.0.0.1:5001/api/upload_log -F "file=@%~dp0sample_log.csv" > nul
:: echo    OK! Blackbox replay started!

echo 5. Starting AI Vision Simulation...
timeout /t 1 > nul
cd /d "%~dp0"
python jetson\main.py

echo.
echo Demo finished.
pause
