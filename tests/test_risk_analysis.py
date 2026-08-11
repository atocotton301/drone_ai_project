import unittest
import sys
import os

# 모듈 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.risk_analysis import calculate_iou, analyze_risk

class TestRiskAnalysis(unittest.TestCase):
    
    def test_calculate_iou_no_overlap(self):
        box1 = [0, 0, 10, 10]
        box2 = [20, 20, 30, 30]
        iou = calculate_iou(box1, box2)
        self.assertEqual(iou, 0.0)

    def test_calculate_iou_full_overlap(self):
        box1 = [0, 0, 10, 10]
        box2 = [0, 0, 10, 10]
        iou = calculate_iou(box1, box2)
        self.assertEqual(iou, 1.0)
        
    def test_calculate_iou_partial_overlap(self):
        box1 = [0, 0, 10, 10]
        box2 = [5, 5, 15, 15]
        iou = calculate_iou(box1, box2)
        self.assertGreater(iou, 0.0)
        self.assertLess(iou, 1.0)

    def test_analyze_risk_armed_person(self):
        # 사람이 무기를 들고 있는 상황 (Bounding Box 겹침)
        detections = [
            {'class_name': 'person', 'bbox': [100, 100, 200, 300], 'conf': 0.9},
            {'class_name': 'weapon', 'bbox': [150, 150, 180, 180], 'conf': 0.8}
        ]
        is_danger, armed_info = analyze_risk(detections)
        self.assertTrue(is_danger)
        self.assertEqual(len(armed_info), 1)

    def test_analyze_risk_unarmed_person_and_dropped_weapon(self):
        # 사람과 무기가 멀리 떨어져 있는 상황 (겹치지 않음)
        detections = [
            {'class_name': 'person', 'bbox': [100, 100, 200, 300], 'conf': 0.9},
            {'class_name': 'weapon', 'bbox': [400, 400, 450, 450], 'conf': 0.8}
        ]
        is_danger, armed_info = analyze_risk(detections)
        self.assertFalse(is_danger)
        self.assertEqual(len(armed_info), 0)

    def test_analyze_risk_multiple_threats(self):
        # 두 명의 무장 인원이 있는 상황
        detections = [
            {'class_name': 'person', 'bbox': [0, 0, 50, 100], 'conf': 0.9},
            {'class_name': 'weapon', 'bbox': [10, 20, 30, 40], 'conf': 0.8},
            {'class_name': 'person', 'bbox': [200, 200, 250, 300], 'conf': 0.9},
            {'class_name': 'weapon', 'bbox': [210, 220, 230, 240], 'conf': 0.8},
            {'class_name': 'smoke', 'bbox': [500, 500, 600, 600], 'conf': 0.9} # 무관한 객체
        ]
        is_danger, armed_info = analyze_risk(detections)
        self.assertTrue(is_danger)
        self.assertEqual(len(armed_info), 2)

if __name__ == '__main__':
    unittest.main()
