#!/bin/bash
# =============================================================
# setup_jetson.sh — Jetson Orin Nano Super 원클릭 셋업 스크립트
# =============================================================
# [사용법]
#   git clone https://github.com/atocotton301/drone_ai_project.git
#   cd drone_ai_project
#   chmod +x jetson/setup_jetson.sh
#   ./jetson/setup_jetson.sh
#
# [수행 작업]
#   1. 시스템 패키지 및 RealSense SDK 저장소 설정
#   2. Swap 메모리 확인 및 OOM 방지
#   3. Python / JetPack 버전 감지 및 CUDA PyTorch & Torchvision 설치
#   4. 의존성 패키지 설치
#   5. 데이터셋 파이프라인 자동 실행 (Auto-Labeling 포함)
#   6. YOLOv8n 학습 및 TensorRT (.engine) 가속 변환
# =============================================================

set -e  # 에러 발생 시 즉시 중단

echo "=============================================="
echo "  🚁 Drone AI — Jetson 셋업 시작"
echo "=============================================="

# 프로젝트 루트 경로 자동 감지
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"
echo "  📁 프로젝트 경로: $PROJECT_ROOT"

# 아키텍처 및 파이썬 버전 확인
ARCH=$(uname -m)
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  🖥  시스템 아키텍처: $ARCH, Python 버전: $PY_VER"

# ============================================================
# Step 1: 시스템 패키지 & RealSense 저장소
# ============================================================
echo ""
echo "[1/6] 🔧 시스템 패키지 및 저장소 설정 중..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    unzip \
    libgl1-mesa-glx \
    v4l-utils

# RealSense APT 저장소 등록 (Ubuntu LTS)
if ! dpkg -s librealsense2-utils >/dev/null 2>&1; then
    echo "  📷 RealSense APT 저장소 등록 중..."
    sudo mkdir -p /etc/apt/keyrings
    curl -sSf https://librealsense.intel.com/Debian/librealsense.pgp | sudo tee /etc/apt/keyrings/librealsense.pgp > /dev/null 2>&1 || true
    echo "deb [signed-by=/etc/apt/keyrings/librealsense.pgp] https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/librealsense.list > /dev/null 2>&1 || true
    sudo apt-get update -qq || true
    sudo apt-get install -y -qq librealsense2-utils librealsense2-dev 2>/dev/null || echo "  ⚠ apt librealsense 설치 스킵 (빌드본 사용 가능)"
fi

echo "  ✓ 시스템 패키지 완료"

# ============================================================
# Step 2: Swap 메모리 확인 (Jetson Orin OOM 방지)
# ============================================================
echo ""
echo "[2/6] 💾 메모리 및 Swap 상태 확인..."
SWAP_TOTAL_MB=$(free -m | awk '/^Swap:/ {print $2}')
if [ -z "$SWAP_TOTAL_MB" ] || [ "$SWAP_TOTAL_MB" -lt 2048 ]; then
    echo "  ⚠  경고: 현재 Swap 메모리가 ${SWAP_TOTAL_MB:-0}MB로 매우 적습니다."
    echo "     Jetson Orin Nano에서 학습 시 OOM(메모리 부족) 종료를 방지하기 위해"
    echo "     최소 4GB~8GB의 스왑 파일 또는 zram 설정을 권장합니다."
else
    echo "  ✓ Swap 메모리 확보됨: ${SWAP_TOTAL_MB}MB"
fi

# ============================================================
# Step 3: Python 의존성 및 PyTorch (CUDA 지원) 설치
# ============================================================
echo ""
echo "[3/6] 🐍 Python 패키지 & PyTorch 확인 중..."

python3 -m pip install --upgrade pip -q

if python3 -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
    TORCH_VER=$(python3 -c "import torch; print(torch.__version__)")
    echo "  ✓ CUDA 가속 지원 PyTorch (${TORCH_VER}) 이미 설치됨"
else
    echo "  ⚠  CUDA PyTorch가 감지되지 않았습니다."
    if [ "$ARCH" = "aarch64" ]; then
        echo "  Jetson(aarch64) 전용 PyTorch 설치를 시도합니다..."
        if [ "$PY_VER" = "3.8" ]; then
            # JetPack 5.x (Ubuntu 20.04)
            pip3 install --no-cache \
                https://developer.download.nvidia.com/compute/redist/jp/v512/pytorch/torch-2.1.0a0+41361538.nv23.06-cp38-cp38-linux_aarch64.whl \
                || pip3 install torch
        elif [ "$PY_VER" = "3.10" ]; then
            # JetPack 6.x (Ubuntu 22.04)
            pip3 install --no-cache \
                https://developer.download.nvidia.com/compute/redist/jp/v60/pytorch/torch-2.3.0a0+ebed944e.nv24.05-cp310-cp310-linux_aarch64.whl \
                || pip3 install torch
        else
            pip3 install torch
        fi
    else
        echo "  x86_64 환경 감지: 기본 PyTorch 설치..."
        pip3 install torch torchvision
    fi
fi

# torchvision 확인 및 설치 (버전 충돌 방지)
if ! python3 -c "import torchvision" 2>/dev/null; then
    echo "  torchvision 설치 중..."
    pip3 install torchvision --no-deps 2>/dev/null || pip3 install torchvision -q
fi

# 프로젝트 공통 의존성 설치
pip3 install -r requirements.txt -q
echo "  ✓ Python 패키지 설치 완료"

# ============================================================
# Step 4: RealSense Python 바인딩 확인
# ============================================================
echo ""
echo "[4/6] 📷 RealSense Python 바인딩 확인 중..."
if python3 -c "import pyrealsense2" 2>/dev/null; then
    echo "  ✓ pyrealsense2 모듈 정상 작동"
else
    echo "  ⚠  pyrealsense2 pip 패키지 설치 시도..."
    pip3 install pyrealsense2 -q 2>/dev/null || {
        echo "  ℹ  ARM64 환경에서는 pyrealsense2가 소스 빌드 또는 apt 바인딩을 사용할 수 있습니다."
        echo "     (카메라 미연결 시 웹캠 Fallback 모드로 안전하게 작동합니다)"
    }
fi

# ============================================================
# Step 5: 데이터셋 구축 + AI 커스텀 학습 & TensorRT 변환
# ============================================================
echo ""
echo "[5/6] 📦 데이터셋 검증 및 AI 모델 학습 시작..."
echo "  (Jetson Orin Nano 최적화: batch 4, imgsz 640)"
echo ""

# Jetson Orin Nano 메모리 안전 설정: GPU 감지, 50 에포크, 배치 4
python3 train_jetson.py \
    --epochs 50 \
    --batch 4 \
    --imgsz 640 \
    --device auto

# ============================================================
# Step 6: 완료 안내
# ============================================================
echo ""
echo "=============================================="
echo "  ✅ Jetson 셋업 및 모델 최적화 완료!"
echo ""
echo "  [드론 AI 온디바이스 실행]"
echo "  python3 jetson/hardware_main.py"
echo ""
echo "  [GCS 웹 관제 대시보드 실행]"
echo "  python3 gcs/app.py"
echo "=============================================="
