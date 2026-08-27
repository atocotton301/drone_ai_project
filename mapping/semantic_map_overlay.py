import math
import time
import json

class ApartmentSemanticMap:
    """
    아파트 실내 / 시가전 다층 구조(Multi-floor) 시맨틱 맵
    - SLAM(또는 Visual Odometry)에서 받은 x, y, z 좌표를 바탕으로 층수 판별
    - 문, 계단, 사람, 위협 요소를 층별 지도에 마킹
    """
    def __init__(self, floor_height=3.0):
        self.floor_height = floor_height
        # floors = { floor_num: [ { 'type': ..., 'x': ..., 'y': ..., 'desc': ... } ] }
        self.floors = {}
        self.drone_path = {} # 층별 드론 이동 경로
        
    def get_floor_from_z(self, z):
        """고도(z)를 기반으로 현재 층수(Floor) 계산. 0~3m: 1층, 3~6m: 2층"""
        floor = math.floor(z / self.floor_height) + 1
        return floor
        
    def add_marker(self, x, y, z, obj_type, desc=""):
        floor = self.get_floor_from_z(z)
        if floor not in self.floors:
            self.floors[floor] = []
            
        marker = {
            'type': obj_type,
            'x': round(x, 2),
            'y': round(y, 2),
            'z': round(z, 2),
            'desc': desc,
            'timestamp': time.time()
        }
        self.floors[floor].append(marker)
        print(f"[MAP] {floor}층에 마커 추가: {obj_type} ({desc}) 좌표: ({x:.1f}, {y:.1f})")
        return marker
        
    def update_drone_position(self, x, y, z):
        floor = self.get_floor_from_z(z)
        if floor not in self.drone_path:
            self.drone_path[floor] = []
            
        self.drone_path[floor].append({'x': round(x, 2), 'y': round(y, 2)})
        
    def export_map_data(self):
        return {
            'floors': self.floors,
            'path': self.drone_path
        }

if __name__ == "__main__":
    # Test
    m = ApartmentSemanticMap()
    m.update_drone_position(0, 0, 1.5)
    m.add_marker(2, 3, 1.5, "NODE_DOOR", "안방 문")
    m.add_marker(5, 5, 1.5, "SURVIVOR", "쓰러진 사람 발견")
    
    # 계단 이동
    m.update_drone_position(6, 6, 4.0) 
    m.add_marker(6, 6, 4.0, "NODE_STAIRS", "계단 진입")
    m.add_marker(10, 10, 4.5, "HAZARD", "2층 화재 발견")
    
    print(json.dumps(m.export_map_data(), indent=2, ensure_ascii=False))
