# 🚁 실내 재난 구조 및 자율 탐색 AI 드론 (GPS-Denied)
**[한성공학경진대회 출품작]**

![GCS Dashboard](https://img.shields.io/badge/UI-BIM%20Style-blue)
![Platform](https://img.shields.io/badge/Platform-Jetson%20Orin%20Nano%20Super-green)
![AI](https://img.shields.io/badge/AI-YOLOv8%20%7C%20TensorRT-orange)
![Sensor](https://img.shields.io/badge/Sensor-Intel%20RealSense%20D435i-blueviolet)

## 📌 프로젝트 소개
본 프로젝트는 **GPS와 외부 통신이 차단된 실내(지하, 재난 현장, 아파트 등)**에서 드론 스스로 비행하며, 내부 구조를 2D 평면도로 실시간 맵핑(Mapping)하고 조난자 및 화재(위험 요소)를 탐지하는 자율비행 AI 시스템입니다.

## ✨ 핵심 기능
- **통신 두절(Failsafe) 대응 자율비행**: MAVSDK 기반 오프보드 제어 및 Optical Flow/LiDAR 융합(H-Flow)을 통한 GPS-OFF 위치 제어
- **온디바이스 비전 AI (TensorRT)**: Jetson Orin Nano Super에서 YOLOv8 커스텀 모델을 가동하여 5개 클래스(`person`, `fire`, `smoke`, `door`, `staircase`) 실시간 탐지 (엣지 컴퓨팅)
- **실시간 2D Occupancy Grid SLAM**: 뎁스 카메라(RealSense) 데이터를 분석하여 드론이 비행하며 벽과 장애물을 인식, 실내 평면도를 스스로 구축
- **BIM/건축 모던 스타일 GCS 관제소**: 모던하고 직관적인 웹 대시보드(Flask 기반)를 통해 드론의 위치, 텔레메트리, 실시간 AI 비전 및 실내 평면도 스트리밍 확인

## 🚀 하드웨어 구성 (Bill of Materials)
- **프레임/FC**: Holybro X500 V2 / Pixhawk 6C
- **엣지 컴퓨터**: NVIDIA Jetson Orin Nano Super
- **센서**: Intel RealSense D435i (RGB-D), Holybro H-Flow (Optical Flow + Lidar)

## 💻 실행 방법 (심사위원 시연용)

### 1. 지상 관제소 (GCS) 서버 구동 (PC / 노트북)
```bash
# 리포지토리 복제
git clone https://github.com/atocotton301/drone_ai_project.git
cd drone_ai_project

# 라이브러리 설치
pip install -r requirements.txt

# 시연용 스크립트 실행 (웹 대시보드 자동 실행)
run_demo.bat
```

### 2. 드론 자율비행 및 맵핑 가동 (Jetson 보드)
> ⚠️ **주의:** Jetson에 RealSense 카메라가 연결되어 있어야 합니다.
```bash
# 젯슨 셋업 (의존성 및 환경 자동 구성)
chmod +x jetson/setup_jetson.sh
./jetson/setup_jetson.sh

# 하드웨어 메인 시스템 가동
python3 jetson/hardware_main.py
```
> **수동 맵핑 테스트 (디버그 모드)**: Jetson 실행 화면에서 `w`, `a`, `s`, `d` 키를 눌러 드론의 가상 위치를 이동시키면, 뎁스 카메라로 바라보는 방향의 벽이 실시간 평면도(Map)로 스캔되는 과정을 GCS에서 확인할 수 있습니다.

## 📁 프로젝트 구조
- `gcs/`: 지상 관제소(GCS) 웹 서버 및 BIM 스타일 UI (`app.py`, `index.html`)
- `jetson/`: 젯슨 보드 탑재용 핵심 실행 파일 (`hardware_main.py`, `inference.py`)
- `mapping/`: 깊이 데이터 기반 2D 평면도 생성 엔진 (`occupancy_map.py`)
- `px4/`: 비행 제어 및 페일세이프 노드 (`vision_flight_control.py`)
- `configs/`, `scripts/`: 데이터셋 설정 및 모델 훈련용 유틸리티

## 🛡️ 안전 및 제약사항
- 실내 비행 전 반드시 QGroundControl에서 `EKF2` 센서 융합 파라미터(`offline_params.txt` 참조)를 설정해야 합니다.
- MAVSDK 연결 실패 시, 코드는 자동으로 모의(Mock) 비행 모드로 전환되어 알고리즘을 안전하게 테스트할 수 있습니다.
