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

def overlay_on_map(detections, depth_map, odom_tf):
    """
    호환성용 헬퍼 함수: 탐지 객체들을 지도 좌표에 투영
    """
    mapped = []
    for d in detections:
        cls_id = d.get('class', d.get('class_id', 0))
        # mock offset
        mapped.append({
            'class_id': cls_id,
            'x': round(odom_tf.get('x', 0.0) + 2.5, 2),
            'y': round(odom_tf.get('y', 0.0) + 2.5, 2)
        })
    return mapped

class SemanticMapper:
    """
    RealSense FOV 및 Depth 기반 3D 위치 계산 맵퍼
    """
    def __init__(self, camera_fov=69.4, image_width=640, image_height=480):
        self.fov = math.radians(camera_fov)
        self.img_w = image_width
        self.img_h = image_height
        self.focal_length = (self.img_w / 2) / math.tan(self.fov / 2)

    def get_world_coordinates(self, bbox, drone_odom, depth_map=None, default_distance=3.0):
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        depth_distance = default_distance
        if depth_map is not None:
            try:
                cx = max(0, min(int(center_x), self.img_w - 1))
                cy = max(0, min(int(center_y), self.img_h - 1))
                dist = float(depth_map[cy, cx])
                if dist > 0.1:
                    depth_distance = dist
            except Exception:
                pass
        
        pixel_offset_x = center_x - (self.img_w / 2)
        angle_offset = math.atan2(pixel_offset_x, self.focal_length)
        absolute_yaw = drone_odom.get('yaw', 0.0) + angle_offset
        
        obj_world_x = drone_odom.get('x', 0.0) + (depth_distance * math.cos(absolute_yaw))
        obj_world_y = drone_odom.get('y', 0.0) + (depth_distance * math.sin(absolute_yaw))
        return round(obj_world_x, 2), round(obj_world_y, 2)

    def process_detections(self, detections, drone_odom, depth_map=None):
        mapped_objects = []
        for det in detections:
            bbox = det.get('bbox', [0, 0, 10, 10])
            wx, wy = self.get_world_coordinates(bbox, drone_odom, depth_map)
            mapped_objects.append({
                'class_name': det.get('class_name', 'unknown'),
                'world_x': wx,
                'world_y': wy,
                'conf': det.get('conf', 1.0)
            })
        return mapped_objects

if __name__ == "__main__":
    m = ApartmentSemanticMap()
    m.update_drone_position(0, 0, 1.5)
    m.add_marker(2, 3, 1.5, "NODE_DOOR", "안방 문")
    m.add_marker(5, 5, 1.5, "SURVIVOR", "쓰러진 사람 발견")
    m.update_drone_position(6, 6, 4.0) 
    m.add_marker(6, 6, 4.0, "NODE_STAIRS", "계단 진입")
    m.add_marker(10, 10, 4.5, "HAZARD", "2층 화재 발견")
    print(json.dumps(m.export_map_data(), indent=2, ensure_ascii=False))

