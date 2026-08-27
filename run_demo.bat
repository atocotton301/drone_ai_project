@echo off
chcp 65001 > nul
echo ===================================================
echo   [한성공학경진대회] 전술 드론 완벽 시연 자동 실행기
echo ===================================================
echo.
echo 1. 지상 통제소(GCS) 서버를 가동합니다...
start "GCS Server" cmd /k "cd /d "%~dp0" && python gcs\app.py"

echo 2. GCS 서버가 시작될 때까지 대기합니다 (3초)...
timeout /t 3 > nul

echo 3. 대시보드 웹사이트를 엽니다...
start http://127.0.0.1:5001

echo 4. 블랙박스(비행 기록) 자동 로드 중...
timeout /t 2 > nul
curl -s -X POST http://127.0.0.1:5001/api/upload_log -F "file=@%~dp0sample_log.csv" > nul
echo    ✓ 블랙박스 재생 시작!

echo 5. 드론 AI 비전(카메라) 시뮬레이션을 시작합니다...
timeout /t 1 > nul
cd /d "%~dp0"
python jetson\main.py

echo.
echo 시연이 종료되었습니다.
pause
