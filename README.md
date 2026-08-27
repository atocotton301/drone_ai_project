# 🚁 실내 GPS-Free 자율비행 드론 AI — 재난 구조 & 전술 정찰

> GPS·네트워크가 차단된 실내/지하 환경에서 자율 비행하며 생존자(사람)·화재·연기·무기를 탐지하는 온디바이스 AI 드론 시스템

## 빠른 시작 (Quick Start)

### 💻 PC에서 파이프라인 검증
```bash
git clone https://github.com/<your-repo>/drone_ai_project.git
cd drone_ai_project
pip install -r requirements.txt

# 데이터 다운로드 + 5 에포크 학습 테스트
python local_train.py
```

### 🚁 Jetson 보드에서 전체 학습 + 실행
```bash
git clone https://github.com/<your-repo>/drone_ai_project.git
cd drone_ai_project

# 한방 셋업 (의존성 설치 → 데이터 다운로드 → 학습 → TensorRT 변환)
chmod +x jetson/setup_jetson.sh
./jetson/setup_jetson.sh

# 드론 AI 실행 (RealSense 연결 후)
python3 jetson/hardware_main.py
```

### 🖥 GCS 대시보드 (노트북)
```bash
python gcs/app.py
# http://localhost:5001 에서 실시간 탐지 영상 + 지도 확인
```

---

## 핵심 개념: 3-OFF + MAP

| OFF | 의미 | 해결 기술 |
|-----|------|-----------|
| **GPS OFF** | 위성 신호 없음 | Optical Flow (H-Flow) + RealSense IMU |
| **NETWORK OFF** | 인터넷 없음 | Jetson 온디바이스 YOLOv8 TensorRT 추론 |
| **AI LINK OFF** | AI 통신 장애 | Pixhawk Failsafe 자동 착륙 |
| **+ MAP** | 실내 지도 생성 | RealSense D435i + SLAM (RTAB-Map) |

---

## 탐지 클래스

| ID | 클래스 | 용도 |
|----|--------|------|
| 0 | `person` | 생존자 탐지 / 위협 인원 |
| 1 | `fire` | 화재 위험구역 설정 |
| 2 | `smoke` | 연기 확산 경로 추적 |
| 3 | `weapon` | 무장 위협 경고 |

---

## 시스템 아키텍처

```
[Intel RealSense D435i]
     │ RGB + Depth + IMU
     ▼
[Jetson Orin Nano Super]
  ├─ YOLOv8n TensorRT  → 탐지 (30+ FPS)
  ├─ RTAB-Map SLAM     → 실내 지도 생성
  ├─ SemanticMapper    → 탐지 좌표 → 지도 마킹
  └─ GCS 송신 (Wi-Fi)  → 실시간 대시보드
     │
[Pixhawk 6C + H-Flow]
  └─ Optical Flow 자율비행 (GPS 없이)
```

---

## 프로젝트 구조

```
drone_ai_project/
├── configs/
│   └── custom_data.yaml      # 학습 데이터셋 설정 (4 클래스)
├── datasets/                 # ⛔ GitHub 제외 (gitignore)
│   └── final/                #    setup_jetson.sh 실행 시 자동 생성
├── gcs/
│   └── app.py                # GCS 지상 관제 대시보드 (Flask)
├── jetson/
│   ├── hardware_main.py      # ✅ Jetson 실제 구동 메인 (RealSense)
│   ├── main.py               # 시뮬레이션 모드 (웹캠)
│   ├── inference.py          # YOLOv8 추론 모듈
│   └── setup_jetson.sh       # ✅ Jetson 원클릭 셋업 스크립트
├── mapping/
│   ├── semantic_map_overlay.py  # 탐지 → 3D 좌표 변환
│   └── visual_slam_setup.py     # ROS 2 SLAM 브리지
├── px4/
│   ├── vision_flight_control.py # MAVSDK 비행 제어
│   └── failsafe_node.py         # 페일세이프 감시
├── scripts/
│   ├── download_dataset.py   # ✅ 데이터셋 자동 다운로드 (COCO/D-Fire)
│   ├── risk_analysis.py      # 생존자/위협/위험 분류 알고리즘
│   └── realsense_driver.py   # RealSense 드라이버 래퍼
├── local_train.py            # ✅ PC에서 파이프라인 검증용 학습
├── train_jetson.py           # ✅ Jetson 전용 전체 학습 스크립트
└── requirements.txt
```

---

## 하드웨어 구성

| 부품 | 모델 |
|------|------|
| 드론 프레임 | Holybro X500 V2 |
| 비행 컨트롤러 | Pixhawk 6C |
| AI 보드 | NVIDIA Jetson Orin Nano Super |
| 위치 센서 | Holybro H-Flow (Optical Flow + LiDAR) |
| 카메라 | Intel RealSense D435i (RGB-D + IMU) |

---

## 개발 워크플로우

```
[로컬 PC]                     [GitHub]                [Jetson 보드]
코드 수정 ──── git push ──▶  repository  ◀── git pull ── ./setup_jetson.sh
                                                              │
                                                         학습 완료
                                                         hardware_main.py 실행
```

1. **PC**: 코드 수정 → `git push`
2. **Jetson**: `git pull` → `python train_jetson.py`
3. **드론 실행**: `python jetson/hardware_main.py`
