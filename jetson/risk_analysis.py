import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from risk_analysis import analyze_risk

# Jetson 환경에서 실시간 탐지 결과 스트림을 받아 risk_analysis 호출 (Mock)
if __name__ == "__main__":
    print("[Jetson Environment] Running real-time risk analysis...")
    test_detections = [
        {'class': 0, 'bbox': [0.1, 0.1, 0.5, 0.5]},
        {'class': 1, 'bbox': [0.15, 0.15, 0.2, 0.2]}
    ]
    analyze_risk(test_detections, map_position=(3.5, -1.2))
