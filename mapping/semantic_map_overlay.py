import math

class SemanticMapper:
    def __init__(self, camera_fov=69.4, image_width=640, image_height=640):
        """
        Intel RealSense D435i의 기본 FOV(약 69도)와 이미지 크기를 기준으로 초기화
        """
        self.fov = math.radians(camera_fov)
        self.img_w = image_width
        self.img_h = image_height
        self.focal_length = (self.img_w / 2) / math.tan(self.fov / 2)

    def get_world_coordinates(self, bbox, drone_odom, depth_map=None, default_distance=3.0):
        """
        BBox 중심점을 기반으로 드론의 현재 위치(Odometry)에서 물체의 실제 3D 월드 좌표를 계산합니다.
        실제 depth_map이 주어지면 물체의 중심점 거리를 사용하고, 없으면 default_distance를 사용합니다.
        
        drone_odom: {'x': float, 'y': float, 'yaw': float(radians)}
        """
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        depth_distance = default_distance
        if depth_map is not None:
            try:
                # 중심 좌표 픽셀화 (경계 초과 방지)
                cx = max(0, min(int(center_x), self.img_w - 1))
                cy = max(0, min(int(center_y), self.img_h - 1))
                
                dist = float(depth_map[cy, cx])
                if dist > 0.1: # 유효한 거리만 적용 (0.0은 노이즈/에러)
                    depth_distance = dist
            except Exception:
                pass
        
        # 이미지 중심으로부터의 픽셀 거리
        pixel_offset_x = center_x - (self.img_w / 2)
        
        # 픽셀 오프셋을 바탕으로 물체의 상대 각도 계산
        angle_offset = math.atan2(pixel_offset_x, self.focal_length)
        
        # 월드 좌표계에서의 물체 절대 각도
        absolute_yaw = drone_odom['yaw'] + angle_offset
        
        # 삼각함수를 이용해 드론 위치로부터 물체의 X, Y 좌표 도출
        obj_world_x = drone_odom['x'] + (depth_distance * math.cos(absolute_yaw))
        obj_world_y = drone_odom['y'] + (depth_distance * math.sin(absolute_yaw))
        
        return round(obj_world_x, 2), round(obj_world_y, 2)

    def process_detections(self, detections, drone_odom, depth_map=None):
        mapped_objects = []
        for det in detections:
            wx, wy = self.get_world_coordinates(det['bbox'], drone_odom, depth_map)
            mapped_objects.append({
                'class_name': det['class_name'],
                'world_x': wx,
                'world_y': wy,
                'conf': det['conf']
            })
        return mapped_objects

if __name__ == "__main__":
    mapper = SemanticMapper()
    dummy_odom = {'x': 0.0, 'y': 0.0, 'yaw': 0.0} # 드론이 0,0에서 앞을 보고 있음
    dummy_det = {'class_name': 'fire', 'bbox': [320, 320, 340, 340], 'conf': 0.9} # 정중앙
    
    wx, wy = mapper.get_world_coordinates(dummy_det['bbox'], dummy_odom, depth_distance=5.0)
    print(f"Object World Coordinates: X={wx}, Y={wy}") # X=5.0, Y=0.0 이어야 함
