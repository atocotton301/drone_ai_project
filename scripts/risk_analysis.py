import math

def calculate_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    if inter_area == 0:
        return 0.0

    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    return inter_area / float(box1_area + box2_area - inter_area)

def analyze_risk(detections, person_class_names=['person'], hazard_class_names=['weapon', 'gun', 'knife', 'fire', 'cell phone'], node_class_names=['stairs', 'escalator', 'elevator']):
    """
    사람과 무기 위치 관계(IoU) 및 위험 요소를 분석하여 무장 인원 및 위험 객체를 식별합니다.
    """
    persons = [d for d in detections if d.get('class_name', '').lower() in person_class_names]
    weapons = [d for d in detections if d.get('class_name', '').lower() in ['weapon', 'gun', 'knife']]
    
    armed_persons = []
    for p in persons:
        for w in weapons:
            if calculate_iou(p['bbox'], w['bbox']) > 0:
                armed_persons.append({'person': p, 'weapon': w})
                break
                
    is_danger = len(armed_persons) > 0
    return is_danger, armed_persons

def analyze_indoor_tactical(detections, current_altitude=0.0):
    """
    아파트 실내 탐색 및 시가전(구조/수색) 전용 리스크 분석
    
    클래스:
      0: person     - 사람 (시가전: 민간인/생존자 또는 적군)
      1: fire       - 화재 (위험 요소)
      2: smoke      - 연기 (시야 차단, 진입 불가)
      3: door       - 문 (새로운 구역 진입 노드)
      4: staircase  - 계단 (층간 이동을 위한 주요 노드)
    """
    targets = []
    events = []
    
    has_threat = False
    found_survivor = False
    stair_detected = False

    for d in detections:
        cname = d['class_name'].lower()
        bbox = d['bbox']
        conf = d.get('confidence', 0.0)

        # 1. 층간 이동 (계단) 인식
        if cname == 'staircase':
            stair_detected = True
            targets.append({'type': 'NODE_STAIRS', 'bbox': bbox, 'desc': '층간 이동 통로 (계단) 발견'})
            events.append("계단 진입로 확보. 층간 맵핑 대기 중.")
            
        # 2. 방 진입 (문) 인식
        elif cname == 'door':
            targets.append({'type': 'NODE_DOOR', 'bbox': bbox, 'desc': '미탐색 구역 (문)'})
            
        # 3. 사람 인식 (구조 및 시가전)
        elif cname == 'person':
            # 아파트/시가전 환경: 드론이 사람을 발견하면 기본적으로 생존자(구조)로 분류하나,
            # 특정 모드에 따라 위협(전투원)으로 식별 가능 (여기서는 구조 최우선)
            found_survivor = True
            targets.append({'type': 'SURVIVOR', 'bbox': bbox, 'desc': '인원(생존자/대상) 식별'})
            events.append("인원 발견! 구조 대상 위치 마킹.")
            
        # 4. 재난 위험 요소
        elif cname in ['fire', 'smoke']:
            has_threat = True
            targets.append({'type': 'HAZARD', 'bbox': bbox, 'desc': f'{cname.upper()} 탐지 - 진입 주의'})
            events.append(f"위험 요소({cname.upper()}) 탐지. 회피 경로 탐색 필요.")

    return {
        "targets": targets,
        "events": events,
        "stair_detected": stair_detected,
        "has_threat": has_threat,
        "found_survivor": found_survivor
    }

