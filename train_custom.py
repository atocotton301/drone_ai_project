from ultralytics import YOLO
import os

def main():
    print("커스텀 AI 모델(사람, 무기, 화재, 연기) 로컬 테스트 학습을 시작합니다...")

    # 1. Base 모델 로드 (가장 가벼운 nano 모델 사용)
    model = YOLO('yolov8n.pt')

    # 2. 로컬 학습
    # yaml 파일의 경로는 절대 경로로 지정하는 것이 안전합니다.
    config_path = os.path.abspath(os.path.join('configs', 'custom_data.yaml'))
    
    print(f"설정 파일: {config_path}")
    print("학습을 진행 중입니다... (에포크: 3)")
    
    results = model.train(
        data=config_path,
        epochs=3,
        imgsz=640,
        batch=2,
        device='cpu', # 현재 로컬 PC 환경을 고려하여 CPU로 고정. 실제 학습 시 0(GPU)으로 변경.
        name='custom_train',
        exist_ok=True # 덮어쓰기 허용
    )

    # 3. 최고 성능 모델 로드 및 변환
    best_model_path = os.path.join('runs', 'detect', 'custom_train', 'weights', 'best.pt')
    
    if os.path.exists(best_model_path):
        print(f"학습 완료! 최고 성능 모델 로드: {best_model_path}")
        best_model = YOLO(best_model_path)
        
        print("Jetson 탑재용 ONNX 포맷 변환 시작...")
        best_model.export(format='onnx')
        print("모든 작업 완료! ONNX 모델이 생성되었습니다.")
    else:
        print("학습된 모델을 찾을 수 없습니다.")

if __name__ == "__main__":
    main()
