# 밀폐 공간 전술 정찰 및 구조를 위한 온디바이스 임베디드 AI 드론

## 1. 프로젝트 소개
본 프로젝트는 GPS와 외부 네트워크가 차단된 밀폐 공간(실내, 지하 등)에서 드론이 독립적으로 비행하며 실내 지도를 생성하고, 인원(person), 위험 물체(weapon), 화재(fire), 연기(smoke)를 탐지하는 온디바이스 임베디드 AI 시스템을 구현합니다.

## 2. 3-OFF + MAP 개념
* **GPS OFF**: Optical Flow, 거리 센서, IMU 기반 비행
* **NETWORK OFF**: 외부 클라우드 없이 Jetson 내부에서 객체 탐지
* **AI LINK OFF**: 통신 장애 시 Position Hold 또는 자동 착륙
* **MAP**: RGB-D 카메라와 SLAM 기술을 이용한 실내 지도 자동 생성 및 객체 위치 표시

## 3. 최종 구현 범위
* RGB-D 카메라 기반 실내 구조 지도 자동 생성
* 오프라인 온디바이스 AI 객체 탐지 (person, weapon, fire, smoke)
* 무장 인원 후보 경고 (사람과 무기 위치 관계 분석)
* **전술 정찰 모드 (Tactical Reconnaissance)**: 인원(Person)과 무기(Weapon)의 위치(BBox) 거리를 계산하여 위협 수준(Threat Level)을 실시간 분석 및 경고
* **재난 구조 모드 (Disaster Rescue)**: 화재(Fire) 및 연기(Smoke) 탐지 시 위험 반경(Danger Zone) 설정 및 요구조자(Person) 접근 위험 알림
* **실시간 AI 추론 및 시뮬레이션 대시보드**: 대회 전시장 등 실제 비행이 제한되는 환경을 대비한 GUI 기반 가상 비행 추론 및 미니맵 연동 시스템 지원
* AI 또는 통신 장애 시 안전 착륙 (Failsafe)

## 3.1 공학경진대회 심사기준 부합성 (한성대학교)
본 프로젝트는 공학경진대회의 5가지 핵심 심사기준을 완벽하게 충족하도록 설계 및 구현되었습니다.
1. **문제 정의의 명확성**: GPS와 외부 통신(클라우드)이 단절된 지하/화재 환경에서 기존 상용 드론이 무용지물이 되는 치명적인 한계를 제기하고 이를 '3-OFF' 상황으로 구체적으로 정의.
2. **공학적 해결 방법**: Jetson 보드의 온디바이스 GPU(TensorRT 가속)와 H-Flow(Optical Flow) 센서를 결합해 클라우드 연결 없이 지연(Latency) 문제를 공학적으로 해결.
3. **구현 수준**: 실제 드론 비행 시연이 가능할 뿐만 아니라, 비행이 불가한 전시 환경을 위해 실시간 객체 탐지 영상과 SLAM 마커가 렌더링되는 **통합 GUI 시뮬레이션 대시보드**를 구축하여 상시 동작 증명 가능.
4. **창의성 및 차별성**: 시판 드론의 통신 단절 시 맹목적 귀환(Return-to-Home) 충돌 한계를 극복하고, "사람과 무기의 거리"를 분석하는 전술적 AI 알고리즘을 도입하여 타 출품작 및 상용품과 명확히 차별화.
5. **실용성 및 확장성**: 국방(대테러 실내 진입 정찰) 및 소방(요구조자 수색) 등 B2G 현장에 즉각 투입 가능한 시나리오로 구성되었으며, ROS 2 통신을 활용하여 군집 드론(Swarm Drones)으로 확장 용이.
## 4. 핵심 기술 및 시스템 구조

### 4.1 하드웨어 구성
* **드론 본체**: Holybro X500 V2 (Pixhawk 6C)
* **AI 보드**: NVIDIA Jetson Orin Nano Super
* **비행 센서**: Holybro H-Flow (Optical Flow, Lidar, IMU)
* **카메라**: Intel RealSense D435i

### 4.2 딥러닝 모델 선정 (YOLOv8 Nano)
* **선정 모델**: YOLOv8n (Nano) 모델 사용
* **선정 이유**: 
  * **실시간 처리(Real-time Processing)**: 비행 중인 드론에서 장애물 및 객체를 즉각적으로 인식하기 위해서는 높은 FPS(Frame Per Second)가 필수적입니다. YOLOv8n은 경량화되어 있어 엣지 디바이스에서도 30FPS 이상의 실시간 탐지가 가능합니다.
  * **정확도와 연산량의 균형**: Nano 모델은 파라미터 수가 적어 메모리 사용량이 적으면서도, person, weapon, fire 등 주요 객체 탐지에서 우수한 mAP(Mean Average Precision)를 보여줍니다.
  * **TensorRT 최적화**: NVIDIA 환경에서 TensorRT를 통한 모델 양자화(Quantization) 및 가속이 매우 용이합니다.

### 4.3 젯슨 보드(NVIDIA Jetson) 도입 이유
* **클라우드 의존성 탈피 (네트워크 단절 대비)**: 지하 공간이나 실내 재난 현장에서는 통신이 불가능할 수 있습니다. 젯슨 보드는 기기 자체(On-Device)에서 딥러닝 추론을 수행할 수 있는 독립된 GPU를 탑재하여 통신 없이도 AI 비전 처리가 가능합니다.
* **강력한 엣지 컴퓨팅 성능**: 젯슨 오린(Jetson Orin) 시리즈는 수십 TOPS의 AI 연산 성능을 제공하여 다중 카메라 스트리밍 처리, SLAM(실내 지도 생성), 객체 탐지를 동시에 수행할 수 있는 병렬 처리 능력을 갖추고 있습니다.
* **SW 생태계**: ROS 2, OpenCV, PyTorch 등 드론 자율비행 및 비전 AI에 필수적인 프레임워크들이 완벽하게 호환 및 최적화되어 지원됩니다.

## 5. 관련 논문 및 기술적 배경 (Literature Review)
본 프로젝트는 다음과 같은 최신 Edge AI 및 무인기(UAV) 연구 동향을 바탕으로 고도화되었습니다.
* **Edge AI for Autonomous Drone Navigation**: 클라우드 기반 처리에서 벗어나 Jetson Nano 등의 엣지 디바이스에서 실시간 의사결정을 수행하는 연구 (TensorFlow Lite / TensorRT 최적화).
* **Vision-based Indoor Perception (e.g., RWA-YOLO)**: 저조도 실내 환경에서 웨이브렛 어텐션 모듈(Wavelet-aware attention)을 결합하여 객체 탐지율을 높이는 비전 기술 연구.
* **UAV Swarms & SLAM Integration**: 객체 탐지 결과를 단순히 화면에 표시하는 것을 넘어, 탐지된 객체의 위치를 3D BIM(Building Information Modeling) 및 2D SLAM 지도에 직접 투영하여 경로 계획(Path Planning)에 활용하는 융합 기술.

## 6. 프로젝트 폴더 역할
* `datasets/`: 학습 데이터셋 관리
* `notebooks/`: Google Colab 학습 노트북
* `scripts/`: 데이터 변환 및 검사 스크립트
* `configs/`: 클래스 매핑 등 설정 파일
* `outputs/`: 벤치마크 결과 및 생성된 지도 데이터
* `reports/`: 데이터셋 소스 및 BOM 등 보고서
* `jetson/`: Jetson 온디바이스 실행 코드
* `mapping/`: ROS 2 및 RTAB-Map 관련 설정 및 코드
* `px4/`: 드론 하드웨어 및 펌웨어 설정 가이드
* `demo/`: 시연 및 촬영 계획
* `tests/`: 로컬 검증용 테스트 코드

## 7. 설치 및 실행 가이드

[목적]
로컬 환경 구성을 위한 의존성 설치

[실행]
`pip install -r requirements.txt`

[정상 결과]
필요한 패키지가 성공적으로 설치됨.

[오류 발생 시]
Python 버전을 확인하고, 가상환경을 재생성 후 시도하세요.

## 8. 향후 발전 방향 및 추천 참가 대회 (Hackathons & Competitions)
본 프로젝트의 완성도를 높여 다음과 같은 국내외 대회 출전을 목표로 할 수 있습니다.

### 국내 주요 대회 및 전시회
* **드론쇼 코리아 (Drone Show Korea)**: 매년 부산 벡스코에서 열리는 아시아 최대 드론 전시. 자율비행 및 AI 융합 기술을 선보일 수 있는 최고의 무대.
* **국제 로봇 콘테스트 (International Robot Contest)**: 지능형 드론 및 로봇 부문이 포함되어 자율 주행 성능을 겨루는 국내 주요 대회.
* **국방부/방위사업청 주관 국방기술 창업 경진대회**: '전술 정찰 및 구조'라는 본 프로젝트의 테마가 국방 및 치안 분야 수요와 완벽하게 일치함.

### 글로벌 및 해커톤
* **AI Co-Scientist Challenge Korea**: 과기정통부 주관 글로벌 AI 해커톤. AI 에이전트를 활용한 과학/기술적 문제 해결 및 드론 혁신 분야에 적합.
* **Drone Defense Hackathon (Europe/Paris)**: 드론, 국방, AI 기술의 교차점을 다루는 48시간 글로벌 해커톤.
* **글로벌 딥테크 해커톤 (AngelHack 등)**: 실내 SLAM과 Edge AI 딥러닝이 융합된 완성도 높은 시스템은 딥테크(Deep Tech) 주제로 글로벌 해커톤에서 수상 가능성이 매우 높음.
