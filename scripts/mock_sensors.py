import time
import math

class MockOdometry:
    """
    하드웨어가 없을 때 드론의 자율 비행(탐색) 궤적을 수학적으로 시뮬레이션합니다.
    추후 RealSense 카메라나 텔레메트리 데이터로 쉽게 교체할 수 있도록 설계되었습니다.
    """
    def __init__(self, speed=0.5, radius=8.0):
        self.start_time = time.time()
        self.speed = speed # 비행 속도 계수
        self.radius = radius # 비행 반경 (m)

    def get_position(self):
        """
        시간의 흐름에 따라 8자 비행(Lissajous curve) 궤적의 X, Y, Yaw 좌표를 반환합니다.
        """
        t = (time.time() - self.start_time) * self.speed
        t_sec = time.time() - self.start_time
        
        # 8자 궤적 계산 (X, Y)
        x = self.radius * math.sin(t)
        y = self.radius * math.sin(t) * math.cos(t)
        
        # 이동 방향(Yaw) 계산
        dx = self.radius * math.cos(t)
        dy = self.radius * (math.cos(t)**2 - math.sin(t)**2)
        yaw = math.atan2(dy, dx)
        
        # 고도(Z축) 시뮬레이션: 시연을 위해 10초 주기마다 층(3m) 변경 (더 다이나믹하게)
        cycle_time = t_sec % 10
        floor = int((t_sec % 30) / 10) # 0, 1, 2 (1F, 2F, 3F)
        next_floor = (floor + 1) % 3
        
        if cycle_time < 7:
            # 7초 동안은 해당 층 유지
            z = 1.5 + floor * 3.0
        else:
            # 7~10초 구간은 다음 층으로 계단/에스컬레이터 이동 (고도 상승/하강)
            progress = (cycle_time - 7) / 3.0
            z = 1.5 + floor * 3.0 + progress * ((next_floor - floor) * 3.0)
        
        return {
            'x': round(x, 2),
            'y': round(y, 2),
            'z': round(z, 2),
            'yaw': yaw
        }

if __name__ == "__main__":
    odom = MockOdometry()
    for _ in range(5):
        print(odom.get_position())
        time.sleep(1)
