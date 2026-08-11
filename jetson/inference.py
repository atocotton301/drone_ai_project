import cv2
from ultralytics import YOLO

class DroneVision:
    def __init__(self, model_path):
        print(f"[DroneVision] Loading model from {model_path}...")
        
        # .engine 확장자(TensorRT)인 경우 Jetson NPU 가속 사용을 명시
        if model_path.endswith('.engine'):
            print("🚀 [NPU 가속] TensorRT 엔진 감지! 100 TOPS 하드웨어 가속 모드로 구동합니다.")
            self.model = YOLO(model_path, task='detect')
        else:
            print("⚠️ [일반 모드] ONNX 또는 PT 모델 감지. 실 기체 탑재 전 TensorRT(.engine) 변환을 권장합니다.")
            self.model = YOLO(model_path, task='detect')
            
        print("[DroneVision] Model loaded successfully.")

    def process_frame(self, frame):
        """
        카메라 프레임을 받아 객체 탐지 결과를 반환합니다.
        반환값: detections 리스트 (각 원소는 {'class': int, 'class_name': str, 'conf': float, 'bbox': [x1, y1, x2, y2]})
        """
        # YOLOv8 추론 실행 (상세 출력 비활성화)
        results = self.model(frame, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # 좌표 추출 및 정수형 변환
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = result.names[class_id]
                
                detections.append({
                    'class': class_id,
                    'class_name': class_name,
                    'conf': conf,
                    'bbox': [int(x1), int(y1), int(x2), int(y2)]
                })
        
        return detections, results[0].plot()

if __name__ == "__main__":
    # 단위 테스트 (직접 실행 시)
    print("This is a module for ONNX inference. Use main.py to run.")
