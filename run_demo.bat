@echo off
chcp 65001 > nul
echo ===================================================
echo   [한성공학경진대회] 전술 드론 완벽 시연 자동 실행기
echo ===================================================
echo.
echo 1. 지상 통제소(GCS) 서버를 가동합니다...
start "GCS Server" cmd /k "cd /d "%~dp0" && python gcs\app.py"

echo 2. 대시보드 웹사이트를 엽니다...
timeout /t 3 > nul
start http://127.0.0.1:5000

echo 3. 드론 AI 비전(카메라) 시뮬레이션을 시작합니다...
timeout /t 2 > nul
cd /d "%~dp0"
python jetson\main.py

echo.
echo 시연이 종료되었습니다.
pause
