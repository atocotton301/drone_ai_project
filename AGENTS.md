# AGENTS.md — 에이전트 역할 분담 및 개발 규칙

## 시스템 구성

이 프로젝트는 **두 개의 머신**이 협력하는 분산 개발 구조입니다.

---

## 🖥️ 노트북 에이전트 (이 PC — 개발 주체)

### 역할
- 코드 작성, 구조 개선, 버그 수정
- 데이터셋 설정 파일 관리 (`configs/custom_data.yaml`)
- 학습 스크립트 수정 (`train_jetson.py`, `local_train.py`)
- GCS 대시보드 코드 수정 (`gcs/`)
- Git 관리 — commit / push
- Jetson에서 실행할 작업이 생기면 코드 반영 후 GitHub push까지 완료

### 제약
- ❌ GPU 없음 → 실제 YOLO 학습 실행 금지
- ❌ TensorRT 변환 실행 금지
- ❌ Jetson 하드웨어 (`hardware_main.py`) 실행 금지

### 코드 작성 기준
- 항상 **Jetson Orin Nano Super** (ARM64, CUDA, JetPack) 환경을 기준으로 작성
- CUDA/TensorRT/ARM64 호환성 우선 고려
- 수정 후 반드시 어떤 파일을 바꿨는지, Jetson에서 어떤 명령을 실행하면 되는지 정리

---

## 🚁 젯슨 에이전트 (Jetson Orin Nano Super — 실행 주체)

### 역할
- `git pull origin main` 으로 최신 코드 수신
- `python3 train_jetson.py` — YOLOv8 커스텀 학습 실행
- TensorRT `.engine` 변환 실행
- `python3 jetson/hardware_main.py` — 실기체 드론 AI 실행
- 학습 결과물, 로그, 수정사항은 `git push`로 노트북에 공유

### 제약
- ❌ 코드 구조 변경, 리팩토링은 하지 않음 (노트북 에이전트 담당)

---

## 탐지 클래스

| ID | 클래스 | 용도 |
|----|--------|------|
| 0 | `person` | 생존자 탐지 / 위협 인원 |
| 1 | `fire` | 화재 위험구역 |
| 2 | `smoke` | 연기 확산 경로 |
| 3 | `door` | 미탐색 구역 진입 경로 |
| 4 | `staircase` | 층간 이동 노드 (다층 지도 트리거) |

---

## 협업 워크플로우

```
[노트북 에이전트]              [GitHub]              [젯슨 에이전트]
코드 수정 ─── git push ──▶  main 브랜치  ◀── git pull ──  학습 실행
버그 수정                                              실기체 구동
GCS 개선                                              git push (결과물)
```

---

## 현재 상태

- ✅ PC 코드 개발 완료 — GitHub push 완료
- 🔄 Jetson 학습 중 (진행 중)
- ⏳ 학습 완료 후 → 노트북에서 `git pull` 로 결과 확인 예정
