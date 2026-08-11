import cv2
import sys
import os
import time
import signal
import signal
import requests
import datetime

# 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from jetson.inference import DroneVision
from scripts.risk_analysis import analyze_risk
from mapping.semantic_map_overlay import SemanticMapper
from scripts.mock_sensors import MockOdometry
from scripts.flight_logger import FlightLogger
import threading
try:
    from px4.vision_flight_control import DroneController
    from px4.failsafe_node import TacticalFailsafeNode
    MAVSDK_AVAILABLE = True
except ImportError:
    MAVSDK_AVAILABLE = False
    print("⚠️ MAVSDK가 설치되어 있지 않아 비행 제어 및 페일세이프 모듈은 모의(Mock)로 작동합니다.")

# =====================================================================
# ⚙️ 하드웨어 세팅 (Jetson 보드 탑재 시 이 부분을 수정하세요!)
# =====================================================================
# GCS(지상 노트북)의 IP 주소를 입력하세요. (현재는 시뮬레이션을 위해 localhost)
# 예시: GCS_SERVER_URL = "http://192.168.0.10:5001"
GCS_SERVER_URL = "http://127.0.0.1:5001"
# =====================================================================

def main():
    print("🚁 [DRONE SYSTEM] 초기화 중...")
    
    # 1. 모듈 초기화
    # 방금 훈련시킨 커스텀 모델 경로로 업데이트 (ONNX 변환본) - OS 독립적인 상대 경로 사용
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_dir, 'runs', 'detect', 'custom_train', 'weights', 'best.onnx')
    if not os.path.exists(model_path):
        print(f"❌ 오류: 모델 파일을 찾을 수 없습니다. 경로: {model_path}")
        return

    vision = DroneVision(model_path)
    mapper = SemanticMapper(image_width=640, image_height=480)
    logger = FlightLogger()
    
    # 페일세이프 모니터링 백그라운드 스레드 가동 (3초 타임아웃)
    if MAVSDK_AVAILABLE:
        failsafe = TacticalFailsafeNode(timeout_limit_sec=3.0)
        monitor_thread = threading.Thread(target=failsafe.timeout_interrupt_isr, daemon=True)
        monitor_thread.start()
        # drone_ctrl = DroneController() # 기체 연결 시 활성화
    else:
        failsafe = None
    
    # 2. 카메라 시뮬레이션 연결 (로컬 PC 웹캠)
    # 웹캠 번호는 보통 0번입니다. (웹캠이 없으면 에러가 날 수 있습니다)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 오류: 카메라(웹캠)를 열 수 없습니다. 샘플 영상으로 대체하거나 카메라를 연결하세요.")
        return
        
    print("✅ [DRONE SYSTEM] 시스템 정상 가동. 'q'를 누르면 종료됩니다.")
    
    global running
    running = True

    def signal_handler(sig, frame):
        global running
        print("\n⚠️ [하드웨어 인터럽트 수신] 시스템을 안전하게 종료합니다 (Graceful Shutdown)...")
        running = False
    
    # 로컬 강제 종료 명령(SIGINT)을 처리하기 위한 설정
    signal.signal(signal.SIGINT, signal_handler)

    # 가상의 드론 비행 시뮬레이터 (추후 실제 센서 통신으로 교체)
    odometry = MockOdometry(speed=0.3, radius=12.0)

    # 경고 텍스트 도배 방지용 타이머
    last_warning_time = 0
    
    # GCS 대시보드 서버 주소 (제거됨 - Radio Silence 모드)
    # gcs_url = "http://127.0.0.01:5000/api/update"

    while running:
        ret, frame = cap.read()
        if not ret:
            print("❌ 오류: 카메라 프레임을 읽을 수 없습니다.")
            break
            
        # 카메라 하드웨어가 정상적으로 프레임을 보내면 Failsafe 갱신
        if failsafe:
            failsafe.receive_camera_heartbeat()
            
        # 프레임 리사이징 (연산 속도 확보)
        frame = cv2.resize(frame, (640, 480))

        # 드론 위치 실시간 업데이트 (시뮬레이션)
        mock_drone_odom = odometry.get_position()

        # [A] 인공지능 탐지 (Inference)
        detections, result_img = vision.process_frame(frame)
        
        # [B] 위험 평가 알고리즘 (Risk Analysis) - 붕괴/재난 시나리오 대응
        # 가상의 계단/에스컬레이터 탐지 주입 (고도가 변환중일 때)
        if abs((mock_drone_odom.get('z', 1.5) - 1.5) % 3.0) > 0.1:
            detections.append({'class_name': 'stairs', 'confidence': 0.99, 'bbox': [300, 200, 340, 280]})

        is_event, event_info = analyze_risk(detections)
        
        # [C] 실내 3D 지도 맵핑 (Semantic Map Overlay)
        mapped_objects = mapper.process_detections(detections, mock_drone_odom)

        # 화면 시각화 (OSD - On Screen Display)
        cv2.putText(result_img, f"GPS-DENIED MODE: ON", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(result_img, f"POS: {mock_drone_odom['x']:.1f}, {mock_drone_odom['y']:.1f} | ALT: {mock_drone_odom.get('z', 1.5):.1f}m", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        if is_event:
            # 화면 경고 메세지 처리
            alert_texts = set([item['type'] for item in event_info])
            if 'SURVIVOR' in alert_texts:
                cv2.putText(result_img, "!! SURVIVOR DETECTED !!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
            elif 'HAZARD' in alert_texts:
                cv2.putText(result_img, "!! HAZARD DETECTED !!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
            elif 'NODE' in alert_texts:
                cv2.putText(result_img, ">>> VERTICAL TRANSITION NODE <<<", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 100, 0), 3)

            # 맵핑 좌표 출력 (3초에 한 번만 출력되도록 스로틀링)
            current_time = time.time()
            if current_time - last_warning_time > 3.0:
                print(f"🚨 [이벤트] 타겟 발견! 지도 좌표: {mapped_objects}")
                last_warning_time = current_time
                
        # 블랙박스 데이터 로깅
        alert_str = "EVENT" if is_event else ""
        logger.log_state("OFFBOARD", mock_drone_odom['x'], mock_drone_odom['y'], mock_drone_odom.get('z', 1.5), mock_drone_odom['yaw'], len(detections), alert_str)
        
        # 결과 화면 출력
        cv2.imshow("Drone AI Simulation", result_img)
        
        # GCS 서버로 실시간 데이터 전송 (하이브리드 모드)
        payload = {
            "status": "NON-GPS OFFBOARD (ACTIVE)",
            "x": mock_drone_odom['x'],
            "y": mock_drone_odom['y'],
            "z": mock_drone_odom.get('z', 1.5),
            "yaw": mock_drone_odom['yaw']
        }
        if is_event and mapped_objects:
            current_time_str = datetime.datetime.now().strftime("%H:%M:%S")
            # 대표 알림 생성
            main_event = event_info[0]
            if main_event['type'] == 'NODE':
                payload['alert'] = f"[{current_time_str}] 수직 이동로({main_event['class']}) 발견! 좌표(X:{mapped_objects[0]['world_x']}, Y:{mapped_objects[0]['world_y']})"
                payload['alert_type'] = 'NODE'
            elif main_event['type'] == 'SURVIVOR':
                payload['alert'] = f"[{current_time_str}] 생존자 발견! 좌표(X:{mapped_objects[0]['world_x']}, Y:{mapped_objects[0]['world_y']})"
                payload['alert_type'] = 'SURVIVOR'
            else:
                payload['alert'] = f"[{current_time_str}] 위험물 발견! 좌표(X:{mapped_objects[0]['world_x']}, Y:{mapped_objects[0]['world_y']})"
                payload['alert_type'] = 'HAZARD'
        
        try:
            # 타임아웃을 0.05초로 주어 통신이 끊겨도 드론 자율비행(루프)이 멈추지 않도록 함
            response = requests.post(f"{GCS_SERVER_URL}/api/update", json=payload, timeout=0.05)
            if response.status_code == 200 and failsafe:
                pass # failsafe.receive_camera_heartbeat() 은 위에서 처리함
                
            # 라이브 영상(JPEG) GCS 서버로 스트리밍 송출
            success, buffer = cv2.imencode('.jpg', result_img, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if success:
                requests.post(f"{GCS_SERVER_URL}/api/upload_frame", data=buffer.tobytes(), headers={'Content-Type': 'application/octet-stream'}, timeout=0.05)
        except:
            # 와이파이가 끊어지면 그냥 무시하고 자율비행(Fire-and-forget) 모드로 자연스럽게 넘어감
            pass

        # 키보드 명령 처리 ('q' 누르면 종료)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('f'):
            print("🚨 [시연 모드] 고의적 카메라 단선(하드웨어 페일세이프) 강제 발동!")
            break
            
        # 사용자가 마우스로 창의 'X' 버튼을 눌러서 강제로 껐을 때 프로그램 종료
        try:
            if cv2.getWindowProperty("Drone AI Simulation", cv2.WND_PROP_AUTOSIZE) == -1:
                break
        except:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("🚁 [DRONE SYSTEM] 시스템 종료.")

if __name__ == "__main__":
    main()
