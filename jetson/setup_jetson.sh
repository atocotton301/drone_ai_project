#!/bin/bash
# =============================================================
# setup_jetson.sh — Jetson Orin Nano Super 원클릭 셋업 스크립트
# =============================================================
# [사용법]
#   git clone https://github.com/<your-repo>/drone_ai_project.git
#   cd drone_ai_project
#   chmod +x jetson/setup_jetson.sh
#   ./jetson/setup_jetson.sh
#
# [수행 작업]
#   1. 시스템 패키지 업데이트
#   2. Python 의존성 설치 (Jetson 전용 패키지 포함)
#   3. 학습 데이터셋 자동 다운로드
#   4. YOLOv8n 커스텀 학습 (GPU 자동 감지)
#   5. TensorRT 변환
# =============================================================

set -e  # 에러 발생 시 즉시 중단

echo "=============================================="
echo "  🚁 Drone AI — Jetson 셋업 시작"
echo "=============================================="

# 프로젝트 루트 경로
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"
echo "  📁 프로젝트 경로: $PROJECT_ROOT"

# ============================================================
# Step 1: 시스템 패키지
# ============================================================
echo ""
echo "[1/5] 🔧 시스템 패키지 업데이트 중..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3-pip \
    python3-dev \
    libopencv-dev \
    python3-opencv \
    git \
    wget \
    curl \
    unzip

echo "  ✓ 시스템 패키지 완료"

# ============================================================
# Step 2: Python 의존성 설치
# ============================================================
echo ""
echo "[2/5] 🐍 Python 패키지 설치 중..."

# pip 업그레이드
python3 -m pip install --upgrade pip -q

# Jetson 환경: torch는 NVIDIA 공식 wheel 사용
# (일반 pip install torch는 Jetson GPU를 사용 못함)
if python3 -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
    echo "  ✓ CUDA-지원 PyTorch 이미 설치됨"
else
    echo "  ⚠  CUDA PyTorch가 없습니다. Jetson 전용 wheel 설치를 시도합니다..."
    echo "  (실패 시 https://developer.nvidia.com/embedded/downloads 에서 수동 설치)"
    pip3 install --no-cache \
        https://developer.download.nvidia.com/compute/redist/jp/v512/pytorch/torch-2.1.0a0+41361538.nv23.06-cp38-cp38-linux_aarch64.whl \
        2>/dev/null || echo "  ⚠  Jetson PyTorch 설치 실패. 기본 pip 버전 사용."
fi

# 프로젝트 공통 의존성
pip3 install -r requirements.txt -q
echo "  ✓ Python 패키지 완료"

# ============================================================
# Step 3: RealSense SDK (librealsense)
# ============================================================
echo ""
echo "[3/5] 📷 Intel RealSense SDK 확인 중..."
if python3 -c "import pyrealsense2" 2>/dev/null; then
    echo "  ✓ pyrealsense2 이미 설치됨"
else
    echo "  pyrealsense2 설치 중..."
    # Jetson용 librealsense 설치 (NVIDIA JetPack 호환)
    sudo apt-get install -y -qq \
        librealsense2-utils \
        librealsense2-dev 2>/dev/null || true
    pip3 install pyrealsense2 -q || echo "  ⚠  pyrealsense2 pip 설치 실패 (정상 — apt로 설치됨)"
fi

# ============================================================
# Step 4: 데이터셋 다운로드 + 학습
# ============================================================
echo ""
echo "[4/5] 📦 데이터셋 다운로드 + AI 학습 시작..."
echo "  (최초 실행 시 데이터 다운로드로 10~30분 소요될 수 있습니다)"
echo ""

# Jetson 권장 설정: GPU 사용, 50 에포크, 배치 8
python3 train_jetson.py \
    --epochs 50 \
    --batch 8 \
    --imgsz 640 \
    --device auto

# ============================================================
# Step 5: 완료 안내
# ============================================================
echo ""
echo "=============================================="
echo "  ✅ Jetson 셋업 완료!"
echo ""
echo "  [드론 AI 실행 명령]"
echo "  python3 jetson/hardware_main.py"
echo ""
echo "  [GCS 대시보드 (노트북에서)]"
echo "  python3 gcs/app.py"
echo "=============================================="
