from flask import Flask, render_template, request, jsonify
import time
import csv
import threading
import io

app = Flask(__name__)

# 드론 상태를 저장하는 전역 변수 (간단한 메모리 DB 역할)
drone_state = {
    "status": "STANDBY",
    "x": 0.0,
    "y": 0.0,
    "z": 0.0,
    "alerts": [],
    "last_update": time.time()
}

# 최신 카메라 프레임 (바이트 단위)
latest_frame = None

@app.after_request
def add_header(response):
    """브라우저가 구버전 HTML을 캐시하지 못하도록 강제 무효화합니다."""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    """GCS 메인 관제 대시보드 화면 반환"""
    return render_template('index.html')

@app.route('/api/update', methods=['POST'])
def update_state():
    """Jetson(드론)에서 보내는 텔레메트리 및 위험 알림 데이터를 수신"""
    global drone_state
    data = request.json
    if not data:
        return jsonify({"success": False}), 400
        
    drone_state['status'] = data.get('status', drone_state['status'])
    drone_state['x'] = data.get('x', drone_state['x'])
    drone_state['y'] = data.get('y', drone_state['y'])
    drone_state['z'] = data.get('z', drone_state['z'])
    
    # 새로운 알림이 있으면 리스트에 추가 (최대 10개 유지)
    new_alert = data.get('alert')
    if new_alert:
        drone_state['alerts'].insert(0, new_alert)
        drone_state['alerts'] = drone_state['alerts'][:10]
        
    drone_state['last_update'] = time.time()
    return jsonify({"success": True})

def replay_worker(csv_content):
    global drone_state
    reader = csv.reader(csv_content.splitlines())
    header = next(reader, None) # skip header
    print("▶️ [Replay] 블랙박스 재생을 시작합니다...")
    
    drone_state['status'] = "REPLAY MODE"
    drone_state['alerts'] = []
    
    for row in reader:
        if len(row) < 7: continue
        # timestamp, mode, x, y, z, yaw, targets, alert
        try:
            drone_state['x'] = float(row[2])
            drone_state['y'] = float(row[3])
            drone_state['z'] = float(row[4])
            
            alert = row[7].strip() if len(row) > 7 else ""
            if alert:
                drone_state['alerts'].insert(0, f"[{row[0]}] {alert} 감지! (X:{drone_state['x']:.1f}, Y:{drone_state['y']:.1f})")
                drone_state['alerts'] = drone_state['alerts'][:10]
                
            drone_state['last_update'] = time.time()
        except:
            pass
        time.sleep(0.1) # 0.1초 간격으로 재생 속도 조절
        
    drone_state['status'] = "REPLAY FINISHED"
    print("⏹️ [Replay] 블랙박스 재생이 완료되었습니다.")

@app.route('/api/upload_log', methods=['POST'])
def upload_log():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
        
    content = file.read().decode('utf-8')
    thread = threading.Thread(target=replay_worker, args=(content,), daemon=True)
    thread.start()
    
    return jsonify({"success": True})

@app.route('/api/upload_frame', methods=['POST'])
def upload_frame():
    """드론에서 보내는 실시간 JPEG 이미지를 수신합니다."""
    global latest_frame
    if request.data:
        latest_frame = request.data
    return "OK", 200

def generate_frames():
    """MJPEG 스트리밍을 위한 제너레이터 함수"""
    global latest_frame
    
    # 기본 대기 이미지 미리 로드
    import os
    fallback_path = os.path.join(app.root_path, 'static', 'images', 'camera_feed.png')
    fallback_frame = b''
    if os.path.exists(fallback_path):
        with open(fallback_path, 'rb') as f:
            fallback_frame = f.read()

    while True:
        frame_to_send = latest_frame if latest_frame is not None else fallback_frame
        
        if frame_to_send:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_to_send + b'\r\n')
        
        time.sleep(0.05) # 최대 20FPS로 제한

@app.route('/video_feed')
def video_feed():
    """웹 브라우저의 <img> 태그에 실시간 영상을 공급합니다."""
    from flask import Response
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/state', methods=['GET'])
def get_state():
    """웹 프론트엔드(UI)에서 현재 드론 상태를 가져가는 API"""
    global drone_state
    
    # [수정] 하이브리드 모드: 3초 이상 실시간 업데이트가 없으면 연결 끊김(FAILSAFE)으로 간주합니다.
    # 단, 블랙박스 리플레이 중일 때는 예외로 합니다.
    if drone_state['status'] not in ["REPLAY MODE", "REPLAY FINISHED"]:
        if time.time() - drone_state['last_update'] > 3.0:
            drone_state['status'] = "CRITICAL FAILSAFE (COMMS LOST)"
        
    return jsonify(drone_state)

if __name__ == '__main__':
    print("[지상 통제소 GCS] 대시보드 서버가 가동되었습니다. (포트: 5001)")
    app.run(host='0.0.0.0', port=5001, debug=False)
