def calculate_iou(box1, box2):
    """
    두 Bounding Box 간의 IoU(Intersection over Union)를 계산합니다.
    box 포맷: [x1, y1, x2, y2]
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    
    if inter_area == 0:
        return 0.0

    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    iou = inter_area / float(box1_area + box2_area - inter_area)
    return iou

def analyze_risk(detections,
                 person_class_names=['person'],
                 hazard_class_names=[
                     # 커스텀 클래스
                     'weapon', 'gun', 'knife', 'fire', 'smoke',
                     # COCO 기본 모델로 탐지 가능한 위험물 대체 클래스들
                     'cell phone',       # 기폭장치/통신장치 위험 가능성
                     'scissors',         # 날카로운 도구
                     'baseball bat',     # 타격 도구
                     'bottle',           # 투척물
                     'fire hydrant',     # 화재 관련 시설
                     'backpack',         # 수상한 짐
                 ],
                 node_class_names=['stairs', 'escalator', 'elevator', 'bench', 'chair']):
    """
    탐지된 객체 리스트를 분석하여 생존자(Survivor), 위험 요소(Hazard), 수직 이동 노드(Node)를 식별합니다.
    반환값: is_event (bool), identified_targets (list of dict)
    """
    targets = []
    is_event = False
    
    for d in detections:
        cname = d['class_name'].lower()
        if cname in node_class_names:
            targets.append({'type': 'NODE', 'class': cname, 'bbox': d['bbox']})
            is_event = True
        elif cname in person_class_names:
            targets.append({'type': 'SURVIVOR', 'class': cname, 'bbox': d['bbox']})
            is_event = True
        elif cname in hazard_class_names:
            targets.append({'type': 'HAZARD', 'class': cname, 'bbox': d['bbox']})
            is_event = True
            
    return is_event, targets

if __name__ == "__main__":
    # Test Data
    test_dets = [
        {'class_name': 'person', 'bbox': [100, 100, 200, 300]},
        {'class_name': 'weapon', 'bbox': [150, 150, 180, 180]}, # Overlaps with person
        {'class_name': 'person', 'bbox': [400, 400, 500, 500]}
    ]
    danger, info = analyze_risk(test_dets)
    print(f"Danger Level High? {danger}")
    print(f"Armed Persons Info: {info}")
