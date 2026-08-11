import csv
import os
import time
from datetime import datetime

class FlightLogger:
    """
    드론의 텔레메트리 및 AI 탐지 이력을 기록하는 블랙박스 시스템입니다.
    """
    def __init__(self, log_dir="logs"):
        self.log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', log_dir))
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 파일명은 실행 시작 시간으로 생성
        filename = datetime.now().strftime("blackbox_%Y%m%d_%H%M%S.csv")
        self.filepath = os.path.join(self.log_dir, filename)
        
        # CSV 헤더 작성
        with open(self.filepath, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Time(s)', 'Mode', 'Pos_X', 'Pos_Y', 'Pos_Z', 'Yaw', 'AI_Detections', 'Alerts'])
            
        self.start_time = time.time()
        print(f"💾 [블랙박스] 데이터 로깅이 시작되었습니다: {self.filepath}")

    def log_state(self, mode, x, y, z, yaw, num_detections, alerts):
        """매 주기마다 현재 상태를 CSV에 한 줄씩 기록합니다."""
        current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        elapsed = round(time.time() - self.start_time, 2)
        
        # 알람 메시지 중 쉼표 처리 (CSV 파싱 오류 방지)
        safe_alerts = str(alerts).replace(',', ';') if alerts else "None"
        
        with open(self.filepath, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([current_time, elapsed, mode, x, y, z, round(yaw, 2), num_detections, safe_alerts])

if __name__ == "__main__":
    # 독립 테스트
    logger = FlightLogger()
    logger.log_state("OFFBOARD", 1.2, -0.5, 1.5, 45.0, 2, "Armed Person Detected")
    print("✅ 로깅 테스트 완료.")
