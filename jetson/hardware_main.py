import cv2
import sys
import os
import time
import signal
import requests
import datetime
import asyncio
import threading

# 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from jetson.inference import DroneVision
from scripts.risk_analysis import analyze_risk
from mapping.semantic_map_overlay import SemanticMapper
from scripts.flight_logger import FlightLogger

# 하드웨어 드라이버 임포트
from scripts.realsense_driver import RealSenseDriver
try:
    from px4.vision_flight_control import DroneController
    from px4.failsafe_node import TacticalFailsafeNode
    MAVSDK_AVAILABLE = True
except ImportError:
    MAVSDK_AVAILABLE = False
    print("⚠️ MAVSDK가 설치되어 있지 않아 비행 제어 및 페일세이프 모듈을 로드할 수 없습니다.")

# =====================================================================
# ⚙️ 실제 하드웨어 구동 세팅
# =====================================================================
# GCS(지상 관제소)의 IP 주소를 입력하세요. (노트북 IP)
GCS_SERVER_URL = "http://192.168.0.100:5001" 
# =====================================================================

running = True

def signal_handler(sig, frame):
    global running
    print("\n⚠️ [하드웨어 인터럽트 수신] 시스템을 안전하게 종료합니다 (Graceful Shutdown)...")
    running = False

def main():
    global running
    print("🚁 [HARDWARE SYSTEM] 젯슨 오린 NX 구동 초기화 중...")
    
    # 로컬 강제 종료 명령(SIGINT)을 처리하기 위한 설정
    signal.signal(signal.SIGINT, signal_handler)

    # 1. 딥러닝 모델 로드 (추후 .engine 파일로 변경 필수)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_dir, 'runs', 'detect', 'custom_train', 'weights', 'best.onnx')
    vision = DroneVision(model_path)
    mapper = SemanticMapper(image_width=640, image_height=480)
    logger = FlightLogger()
    
    # 2. 리얼센스 카메라 초기화
    cam = RealSenseDriver(width=640, height=480, fps=30)
    cam.start()
    if not cam.is_connected:
        print("❌ 치명적 오류: 리얼센스 카메라 초기화에 실패했습니다. 비행을 중단합니다.")
        return

    # 3. 페일세이프 및 드론 컨트롤러 초기화 (향후 활성화)
    if MAVSDK_AVAILABLE:
        failsafe = TacticalFailsafeNode(timeout_limit_sec=3.0)
        monitor_thread = threading.Thread(target=failsafe.timeout_interrupt_isr, daemon=True)
        monitor_thread.start()
        # TODO: 실제 Pixhawk 시리얼 포트(예: /dev/ttyTHS1)에 연결
        # drone_ctrl = DroneController(system_address="serial:///dev/ttyTHS1:921600")
        # asyncio.run(drone_ctrl.connect())
    else:
        failsafe = None
        
    print("✅ [HARDWARE SYSTEM] 시스템 정상 가동. (Ctrl+C로 종료)")
    last_warning_time = 0
    
    # 단순 VIO(Visual Odometry) 흉내를 내기 위한 위치 변수
    drone_x, drone_y, drone_yaw = 0.0, 0.0, 0.0

    while running:
        # 리얼센스에서 RGB 프레임과 미터 단위의 Depth 배열을 받아옴
        color_frame, depth_map = cam.get_frames()
        if color_frame is None:
            continue
            
        if failsafe:
            failsafe.receive_camera_heartbeat()

        # 실제로는 리얼센스의 IMU + VSLAM 알고리즘을 통해 계산해야 하지만 
        # 여기서는 화면 중앙의 Depth 값을 Z 고도로 임시로 사용합니다.
        h, w = depth_map.shape
        drone_z = float(depth_map[h//2, w//2])
        if drone_z == 0.0: drone_z = 1.5 # 노이즈 방지용 디폴트값

        mock_drone_odom = {'x': drone_x, 'y': drone_y, 'z': drone_z, 'yaw': drone_yaw}

        # [A] YOLOv8 AI 객체 탐지
        detections, result_img = vision.process_frame(color_frame)
        
        # [B] 위험 평가 알고리즘 (Risk Analysis)
        is_event, event_info = analyze_risk(detections)
        
        # [C] 3D 지도 맵핑 (실제 RealSense Depth 데이터 반영)
        mapped_objects = mapper.process_detections(detections, mock_drone_odom, depth_map)

        # 화면 시각화 (OSD)
        cv2.putText(result_img, f"HW MODE: ON (RealSense D435i)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(result_img, f"ALT (Depth): {drone_z:.2f}m", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        if is_event:
            alert_texts = set([item['type'] for item in event_info])
            if 'SURVIVOR' in alert_texts:
                cv2.putText(result_img, "!! SURVIVOR DETECTED !!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
            elif 'HAZARD' in alert_texts:
                cv2.putText(result_img, "!! HAZARD DETECTED !!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)

        # GCS 서버로 실시간 데이터 전송
        payload = {
            "status": "HARDWARE (JETSON ORIN NX)",
            "x": mock_drone_odom['x'],
            "y": mock_drone_odom['y'],
            "z": mock_drone_odom['z'],
            "yaw": mock_drone_odom['yaw']
        }
        
        if is_event and mapped_objects:
            current_time_str = datetime.datetime.now().strftime("%H:%M:%S")
            main_event = event_info[0]
            payload['alert'] = f"[{current_time_str}] {main_event['type']} 발견! 좌표(X:{mapped_objects[0]['world_x']}, Y:{mapped_objects[0]['world_y']})"
            payload['alert_type'] = main_event['type']
        
        try:
            requests.post(f"{GCS_SERVER_URL}/api/update", json=payload, timeout=0.05)
            # 라이브 영상(JPEG) 송출
            success, buffer = cv2.imencode('.jpg', result_img, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if success:
                requests.post(f"{GCS_SERVER_URL}/api/upload_frame", data=buffer.tobytes(), headers={'Content-Type': 'application/octet-stream'}, timeout=0.05)
        except:
            pass # GCS 통신 끊김 무시

        # (디버그용) 화면 출력
        cv2.imshow("Hardware AI System", result_img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 자원 정리
    cam.stop()
    cv2.destroyAllWindows()
    print("🚁 [HARDWARE SYSTEM] 시스템 완전 종료.")

if __name__ == "__main__":
    main()
