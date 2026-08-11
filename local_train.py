from ultralytics import YOLO
import os

print("🚀 로컬 환경에서 드론 AI(YOLO) 학습 및 변환을 시작합니다...")

# 1. 모델 로드
model = YOLO('yolov8n.pt')

# 2. 로컬 CPU에서 5 에포크 테스트 학습
print("⏳ 학습을 진행 중입니다. CPU 환경이라 1~2분 정도 소요될 수 있습니다.")
results = model.train(
    data='coco8.yaml',
    epochs=5,
    imgsz=640,
    batch=16,
    device='cpu',  # 회원님 PC에 GPU가 없어도 무조건 돌아가도록 CPU 강제 할당
    seed=42
)

# 3. 학습된 최고 성능의 모델 다시 불러오기
best_model_path = 'runs/detect/train/weights/best.pt'
if os.path.exists(best_model_path):
    print(f"✅ 학습 완료! 최고 성능 모델을 로드합니다: {best_model_path}")
    model = YOLO(best_model_path)
else:
    print("⚠️ 베스트 모델을 찾지 못해 기본 모델로 진행합니다.")

# 4. ONNX 변환
print("🔄 Jetson 보드용 ONNX 포맷으로 변환 중...")
model.export(format='onnx')

print("🎉 모든 작업이 완료되었습니다! ONNX 파일이 runs/detect/train/weights/ 폴더에 저장되었습니다.")
