import numpy as np
import cv2

class OccupancyGridMapper:
    def __init__(self, map_size_m=30.0, resolution=0.05):
        """
        map_size_m: 맵의 실제 물리적 크기 (가로세로 30m)
        resolution: 1픽셀이 나타내는 미터 (0.05 = 5cm)
        """
        self.resolution = resolution
        self.width = int(map_size_m / resolution)
        self.height = int(map_size_m / resolution)
        
        # 어두운 회색으로 미탐색(Unexplored) 구역 초기화
        self.map_img = np.full((self.height, self.width, 3), 40, dtype=np.uint8)
        
        # 시작 위치 (정중앙)
        self.origin_x = self.width // 2
        self.origin_y = self.height // 2

    def _world_to_map(self, x, y):
        # 드론 앞이 x, 오른쪽이 y라고 가정 (항공 역학 표준 NED)
        px = self.origin_x + int(y / self.resolution)
        py = self.origin_y - int(x / self.resolution)
        return px, py

    def update_map(self, depth_array, odom_x, odom_y, odom_yaw, fov_deg=69.0):
        """
        depth_array: 카메라 깊이 프레임 (가장 핵심)
        odom_x, y, yaw: 드론 위치 및 회전각
        """
        if depth_array is None:
            return self.map_img
            
        h, w = depth_array.shape
        drone_px, drone_py = self._world_to_map(odom_x, odom_y)
        
        # 드론이 지나간 자리는 녹색 궤적으로 표시 (안전 구역)
        cv2.circle(self.map_img, (drone_px, drone_py), 3, (0, 255, 0), -1)
        
        # 중앙 수평선 1줄을 가져와 2D 레이저 스캔(Lidar)처럼 활용
        mid_row = depth_array[h // 2, :]
        
        # 카메라 화각(FOV)에 맞춰 각도 배열 생성
        angles = np.linspace(-fov_deg / 2, fov_deg / 2, w)
        
        for i, z in enumerate(mid_row):
            if z <= 0.2 or z > 8.0:
                continue # 노이즈(너무 가깝거나 너무 먼 것) 제거
                
            # 장애물 절대 각도
            world_angle = np.radians(odom_yaw + angles[i])
            
            # 장애물 위치 (X, Y)
            obs_x = odom_x + z * np.cos(world_angle)
            obs_y = odom_y + z * np.sin(world_angle)
            
            obs_px, obs_py = self._world_to_map(obs_x, obs_y)
            
            if 0 <= obs_px < self.width and 0 <= obs_py < self.height:
                # 붉은색 점으로 벽/장애물 마킹 (Occupied)
                self.map_img[obs_py, obs_px] = (0, 0, 255)
                
        # 보기 좋게 가이드라인 테두리 추가
        cv2.rectangle(self.map_img, (0, 0), (self.width-1, self.height-1), (255,255,255), 1)
        return self.map_img

    def get_map_jpeg(self):
        """GCS 서버로 전송하기 위해 JPEG 변환"""
        success, buffer = cv2.imencode('.jpg', self.map_img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if success:
            return buffer.tobytes()
        return None
