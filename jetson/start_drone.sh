#!/bin/bash
# ==========================================
# Tactical Drone AI System Autostart Script
# ==========================================
# 드론 전원 인가 시 시스템이 자동으로 초기화되고 메인 로직이 실행됩니다.

echo "=========================================="
echo "🚁 젯슨 보드 자율 비행 시스템 가동 시작"
echo "=========================================="

# 1. 젯슨 보드 최고 성능 모드 강제 적용 (NVPModel MAXN)
echo "[1/4] 전력 모드 최적화 (MAXN 적용)..."
sudo nvpmodel -m 0 || echo "nvpmodel 명령어를 찾을 수 없거나 이미 최적화됨."
sudo jetson_clocks || echo "jetson_clocks 명령어를 찾을 수 없음."

# 2. 리얼센스 카메라 초기화 대기 (USB 디바이스 로드 시간 확보)
echo "[2/4] 광학 센서(RealSense) 마운트 대기 중 (3초)..."
sleep 3

# 3. 프로젝트 폴더로 이동 (스크립트 위치 기준 자동 감지)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"
echo "  📁 실행 경로: $PROJECT_ROOT"

# 4. 메인 통합 파이썬 스크립트 실행 (하드웨어 모드 우선 실행)
echo "[3/4] 메인 온디바이스 AI 파이프라인 가동..."
if [ -f "jetson/hardware_main.py" ]; then
    python3 jetson/hardware_main.py &
else
    python3 jetson/main.py &
fi
MAIN_PID=$!

echo "[4/4] 시스템 가동 완료. PID: $MAIN_PID"
echo "⚠️ 시스템을 중지하려면 'kill $MAIN_PID' 를 입력하세요."
wait $MAIN_PID
echo "시스템이 종료되었습니다."
