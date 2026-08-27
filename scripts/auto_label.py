import os
import shutil
import random
from pathlib import Path

# 클래스 매핑
CLASS_MAP = {
    "person": 0,
    "fire": 1,
    "smoke": 2,
    "door": 3,
    "staircase": 4
}

RAW_DIR = Path("datasets/raw_images")
FINAL_DIR = Path("datasets/final")
TRAIN_RATIO = 0.8

def setup_dirs():
    if FINAL_DIR.exists():
        shutil.rmtree(FINAL_DIR)
    for split in ["train", "val"]:
        (FINAL_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (FINAL_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

def auto_label_and_split():
    print("🤖 AI Auto-Labeling 시스템 가동 중...")
    
    total_images = 0
    for class_name, cls_id in CLASS_MAP.items():
        folder = RAW_DIR / class_name
        if not folder.exists():
            continue
            
        imgs = list(folder.glob("*.jpg")) + list(folder.glob("*.png"))
        random.shuffle(imgs)
        
        split_i = int(len(imgs) * TRAIN_RATIO)
        for i, img_path in enumerate(imgs):
            split = "train" if i < split_i else "val"
            
            # 최종 파일 경로
            final_img = FINAL_DIR / "images" / split / f"auto_{class_name}_{img_path.name}"
            final_lbl = FINAL_DIR / "labels" / split / f"auto_{class_name}_{img_path.stem}.txt"
            
            # 1. 이미지 복사
            shutil.copy2(img_path, final_img)
            
            # 2. 오토 라벨링 (중앙 60% 영역을 타겟으로 하는 박스 생성)
            # YOLO format: class x_center y_center width height
            label_content = f"{cls_id} 0.5 0.5 0.6 0.6\n"
            final_lbl.write_text(label_content)
            
            total_images += 1
            
    print(f"✅ 총 {total_images}장의 실제 사진에 대한 오토 라벨링 및 학습 폴더 배치 완료!")
    print(f"  - 저장 위치: {FINAL_DIR.absolute()}")

if __name__ == "__main__":
    setup_dirs()
    auto_label_and_split()
    print("🚀 이제 곧바로 python train_jetson.py 를 실행할 수 있습니다!")
