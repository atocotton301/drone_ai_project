import sys
import os
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mapping'))
from semantic_map_overlay import overlay_on_map

def test_overlay_on_map():
    detections = [{'class': 0}, {'class': 2}]
    depth_map = []  # 가짜 깊이 영상
    odom_tf = {'x': 1.0, 'y': 1.0}
    
    result = overlay_on_map(detections, depth_map, odom_tf)
    assert len(result) == 2
    assert result[0]['class_id'] == 0
    assert result[1]['class_id'] == 2
    assert result[0]['x'] == 3.5  # 1.0 + 2.5 (Mock 거리)
    assert result[0]['y'] == 3.5
