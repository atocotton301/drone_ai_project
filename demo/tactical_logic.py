import math

def calculate_center(bbox):
    """Calculate the center (x, y) of a bounding box [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2, (y1 + y2) / 2)

def calculate_distance(bbox1, bbox2):
    """Calculate Euclidean distance between the centers of two bounding boxes."""
    c1 = calculate_center(bbox1)
    c2 = calculate_center(bbox2)
    return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

def assess_threat_level(detections, distance_threshold=200):
    """
    Evaluate threat level based on the proximity of 'person' and 'weapon'.
    detections: list of dicts, e.g., [{'class': 'person', 'bbox': [10, 10, 50, 100]}, ...]
    Returns: (ThreatLevel: str, ThreatPairs: list)
    """
    persons = [d for d in detections if d['class'] == 'person']
    weapons = [d for d in detections if d['class'] == 'weapon']
    
    threat_pairs = []
    for p in persons:
        for w in weapons:
            dist = calculate_distance(p['bbox'], w['bbox'])
            if dist < distance_threshold:
                threat_pairs.append({'person': p, 'weapon': w, 'distance': dist})
                
    if threat_pairs:
        return "HIGH", threat_pairs
    elif weapons:
        return "MEDIUM", []
    else:
        return "LOW", []

def assess_danger_zone(detections, distance_threshold=300):
    """
    Evaluate danger zone based on proximity of 'person' and 'fire'/'smoke'.
    """
    persons = [d for d in detections if d['class'] == 'person']
    hazards = [d for d in detections if d['class'] in ['fire', 'smoke']]
    
    danger_pairs = []
    for p in persons:
        for h in hazards:
            dist = calculate_distance(p['bbox'], h['bbox'])
            if dist < distance_threshold:
                danger_pairs.append({'person': p, 'hazard': h, 'distance': dist})
                
    if danger_pairs:
        return "CRITICAL", danger_pairs
    elif hazards:
        return "WARNING", []
    else:
        return "SAFE", []
