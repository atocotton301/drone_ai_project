# 공개 객체 탐지 데이터셋 조사

## 데이터셋 후보

| 데이터셋 이름 | 제공 기관/저자 | 원본 페이지 | 다운로드 주소 | 라이선스 | 이미지 수 | 예상 용량 | 포함 클래스 | 라벨 형식 | 회원가입 | API 키 | 추천 | 위험 | 중복 | 날짜 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COCO 2017 | Microsoft | cocodataset.org | [링크] | CC BY 4.0 | 118K | 18GB | person | COCO JSON | 불필요 | 불필요 | O | 없음 | 낮음 | 2026-07 |
| Pascal VOC 2012 | VOC | host.robots.ox.ac.uk | [링크] | 비상업적 | 11K | 2GB | person | VOC XML | 불필요 | 불필요 | O | 없음 | 낮음 | 2026-07 |
| CrowdHuman | Megvii | crowdhuman.org | [링크] | 비상업적 | 15K | 3GB | person | JSON | 필요 | 불필요 | O | 가려짐(occlusion) 많음 | 낮음 | 2026-07 |
| Roboflow Universe Fire/Smoke | 커뮤니티 | universe.roboflow.com | [링크] | CC BY 4.0 등 | 5K | 500MB | fire, smoke | YOLO | 필요 | 필요 | O | 라벨 품질 편차 | 높음 | 2026-07 |
| D-Fire | Github | github.com/m4hn/dfire | [링크] | 오픈 | 3K | 300MB | fire, smoke | YOLO | 불필요 | 불필요 | O | 없음 | 낮음 | 2026-07 |
| Weapon Detection Dataset | Roboflow | universe.roboflow.com | [링크] | CC BY 4.0 등 | 4K | 400MB | handgun, rifle | YOLO | 필요 | 필요 | O | 총기 모형 등 품질 | 높음 | 2026-07 |
| UoC Handgun Dataset | Univ of Granada | [링크] | [링크] | 학술 | 3K | 300MB | handgun | XML | 불필요 | 불필요 | O | 영화 장면 많음 | 낮음 | 2026-07 |

## 데이터셋 조합 추천

**추천 선택**
* **person**: COCO 2017 (person 클래스만 추출) + Pascal VOC (실내 person 데이터 위주)
* **weapon**: UoC Handgun Dataset + Roboflow Universe 엄선 데이터
* **fire, smoke**: D-Fire 데이터셋

**추천 이유**
* 라이선스 문제없이 공학경진대회 목적 부합
* 용량 2~3GB 수준으로 압축 가능 (전체 COCO가 아닌 person만 필터링)
* D-Fire는 연기와 화재가 균형 있게 포함되어 있음.

**내가 확인할 내용**
* COCO 데이터셋 전체 18GB 다운로드 후 필터링할지, 아니면 FiftyOne 등을 사용해 person만 다운로드할지 결정 필요.
* Roboflow Universe 데이터셋 다운로드를 위한 API 키 입력 여부
