from ultralytics import YOLO

print("훈련된 커스텀 모델을 로드하여 테스트를 시작합니다...")
model = YOLO(r"c:\AI project\drone_ai_project\runs\detect\runs\detect\custom_train\weights\best.pt")

print("샘플 이미지 하나를 로드하여 분석 중...")
results = model.predict(source=r"c:\AI project\drone_ai_project\datasets\sample\images\train\sample_000.jpg", save=True)

print(f"✅ 분석 완료! 결과 사진이 {results[0].save_dir} 폴더에 저장되었습니다.")
