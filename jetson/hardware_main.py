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
from scripts.risk_analysis import analyze_indoor_tactical
from mapping.semantic_map_overlay import ApartmentSemanticMap
from mapping.occupancy_map import OccupancyGridMapper
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
GCS_SERVER_URL = "http://127.0.0.1:5001" 
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

    # 1. 딥러닝 모델 로드 (우선순위: .engine -> .onnx -> .pt -> yolov8n.pt)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    weights_dir = os.path.join(base_dir, 'runs', 'detect', 'custom_train', 'weights')
    
    candidates = [
        os.path.join(weights_dir, 'best.engine'),
        os.path.join(weights_dir, 'best.onnx'),
        os.path.join(weights_dir, 'best.pt'),
        os.path.join(base_dir, 'yolov8n.pt')
    ]
    model_path = next((p for p in candidates if os.path.exists(p)), 'yolov8n.pt')
    print(f"📦 [Model Load] 선택된 모델: {model_path}")
    vision = DroneVision(model_path)
    
    # 다층 아파트 실내 지도 및 2D 평면도(Occupancy Grid) 초기화
    mapper = ApartmentSemanticMap(floor_height=3.0)
    grid_mapper = OccupancyGridMapper(map_size_m=30.0, resolution=0.05)
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
    else:
        failsafe = None
        
    print("✅ [HARDWARE SYSTEM] 시스템 정상 가동. (Ctrl+C로 종료)")
    
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
        
        # [B] 아파트 실내/전술 위험 평가 알고리즘
        analysis = analyze_indoor_tactical(detections, current_altitude=drone_z)
        
        # [C] 다층 3D 지도 맵핑 및 2D 실시간 평면도 생성
        mapper.update_drone_position(drone_x, drone_y, drone_z)
        grid_mapper.update_map(depth_map, drone_x, drone_y, drone_yaw)
        
        for target in analysis["targets"]:
            # 시야각(FOV) 기반 좌표 투영 공식은 추후 적용, 현재는 드론 좌표 근처로 마킹
            mapper.add_marker(drone_x + 1.0, drone_y + 1.0, drone_z, target['type'], target['desc'])

        # 화면 시각화 (OSD)
        cv2.putText(result_img, f"HW MODE: ON (RealSense D435i)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(result_img, f"ALT (Depth): {drone_z:.2f}m", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        if analysis["targets"]:
            if analysis["found_survivor"]:
                cv2.putText(result_img, "!! SURVIVOR DETECTED !!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
            if analysis["has_threat"]:
                cv2.putText(result_img, "!! HAZARD (FIRE/SMOKE) !!", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
            if analysis["stair_detected"]:
                cv2.putText(result_img, "STAIRCASE NODE (FLOOR CHANGE)", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 3)

        # GCS 서버로 실시간 데이터 전송
        payload = {
            "status": "HARDWARE (JETSON ORIN NX)",
            "x": mock_drone_odom['x'],
            "y": mock_drone_odom['y'],
            "z": mock_drone_odom['z'],
            "yaw": mock_drone_odom['yaw']
        }
        
        if analysis["events"]:
            current_time_str = datetime.datetime.now().strftime("%H:%M:%S")
            payload['alert'] = f"[{current_time_str}] {analysis['events'][0]}"
            payload['alert_type'] = analysis["targets"][0]['type']
        
        try:
            requests.post(f"{GCS_SERVER_URL}/api/update", json=payload, timeout=0.05)
            
            # 라이브 영상(JPEG) 송출
            success, buffer = cv2.imencode('.jpg', result_img, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if success:
                requests.post(f"{GCS_SERVER_URL}/api/upload_frame", data=buffer.tobytes(), headers={'Content-Type': 'application/octet-stream'}, timeout=0.05)
                
            # 실시간 평면도(Map) 영상 송출
            map_jpeg = grid_mapper.get_map_jpeg()
            if map_jpeg:
                requests.post(f"{GCS_SERVER_URL}/api/upload_map", data=map_jpeg, headers={'Content-Type': 'application/octet-stream'}, timeout=0.05)
                
        except:
            pass # GCS 통신 끊김 무시

        # [자동 시연 모드] 키보드 입력 없이도 카메라 방향으로 천천히 전진 (루프당 3cm)
        drone_x += 0.03

        # (디버그 및 테스트용) 화면 출력 및 키보드로 맵핑 조종 기능 (WASD)
        try:
            cv2.imshow("Hardware AI System", result_img)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('w'): drone_x += 0.2
            elif key == ord('s'): drone_x -= 0.2
            elif key == ord('a'): drone_y -= 0.2
            elif key == ord('d'): drone_y += 0.2
            elif key == ord('z'): drone_yaw -= 5.0 # 좌회전
            elif key == ord('c'): drone_yaw += 5.0 # 우회전
        except Exception:
            pass # GUI가 없는 환경(백그라운드) 무시


    # 자원 정리
    cam.stop()
    cv2.destroyAllWindows()
    print("🚁 [HARDWARE SYSTEM] 시스템 완전 종료.")

if __name__ == "__main__":
    main()
