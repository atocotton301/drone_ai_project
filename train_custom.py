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
        exist_ok=True, # 덮어쓰기 허용
        
        # === [데이터 증강 (Data Augmentation) 옵션] ===
        # 어두운 한국식 복도, 흔들리는 드론 카메라 등을 시뮬레이션
        hsv_h=0.015,   # 이미지 색조 변환 (조명 변화 시뮬레이션)
        hsv_s=0.7,     # 채도 변환 (흐린 날씨, 센서 노이즈)
        hsv_v=0.4,     # 명도 변환 (어두운 복도 환경 시뮬레이션)
        degrees=15.0,  # 드론의 롤링/피칭에 의한 화면 회전 (±15도)
        translate=0.1, # 화면 흔들림 시뮬레이션
        scale=0.5,     # 크기 변환 (거리에 따른 물체 크기 변화)
        fliplr=0.5,    # 좌우 반전 (데이터 2배 뻥튀기 효과)
        mosaic=1.0,    # 4장의 사진을 하나로 합쳐서 훈련 (작은 타겟 탐지율 극강 상승)
        mixup=0.2      # 두 이미지를 겹침 (복잡한 배경에서의 강건함 증가)
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
