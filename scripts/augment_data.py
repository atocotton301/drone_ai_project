import cv2
import numpy as np
import os
import glob
import random
from pathlib import Path

TRAIN_IMG_DIR = Path("datasets/final/images/train")
TRAIN_LBL_DIR = Path("datasets/final/labels/train")

def augment_image_and_label(img_path, lbl_path):
    img = cv2.imread(str(img_path))
    if img is None: return
    
    with open(lbl_path, "r") as f:
        labels = f.readlines()
        
    base_name = img_path.stem
    
    # 1. 밝기 증가 (Brightness +)
    bright = cv2.convertScaleAbs(img, alpha=1.2, beta=30)
    cv2.imwrite(str(TRAIN_IMG_DIR / f"{base_name}_bright.jpg"), bright)
    with open(TRAIN_LBL_DIR / f"{base_name}_bright.txt", "w") as f:
        f.writelines(labels)
        
    # 2. 어둡게 (Darkness)
    dark = cv2.convertScaleAbs(img, alpha=0.8, beta=-30)
    cv2.imwrite(str(TRAIN_IMG_DIR / f"{base_name}_dark.jpg"), dark)
    with open(TRAIN_LBL_DIR / f"{base_name}_dark.txt", "w") as f:
        f.writelines(labels)
        
    # 3. 좌우 반전 (Horizontal Flip)
    flipped = cv2.flip(img, 1)
    cv2.imwrite(str(TRAIN_IMG_DIR / f"{base_name}_flip.jpg"), flipped)
    # 라벨 박스의 x_center도 반전시켜야 함
    with open(TRAIN_LBL_DIR / f"{base_name}_flip.txt", "w") as f:
        for line in labels:
            parts = line.strip().split()
            if len(parts) == 5:
                cls_id, x, y, w, h = parts
                new_x = 1.0 - float(x)
                f.write(f"{cls_id} {new_x:.6f} {y} {w} {h}\n")
                
    # 4. 블러 추가 (Gaussian Blur) - 연기 낀 상황 묘사
    blurred = cv2.GaussianBlur(img, (15, 15), 0)
    cv2.imwrite(str(TRAIN_IMG_DIR / f"{base_name}_blur.jpg"), blurred)
    with open(TRAIN_LBL_DIR / f"{base_name}_blur.txt", "w") as f:
        f.writelines(labels)

    # 5. 가우시안 노이즈 (저조도 드론 카메라 시뮬레이션)
    row, col, ch = img.shape
    mean = 0
    var = 400
    sigma = var**0.5
    gauss = np.random.normal(mean, sigma, (row, col, ch)).astype('float32')
    noisy = np.clip(img.astype('float32') + gauss, 0, 255).astype('uint8')
    cv2.imwrite(str(TRAIN_IMG_DIR / f"{base_name}_noise.jpg"), noisy)
    with open(TRAIN_LBL_DIR / f"{base_name}_noise.txt", "w") as f:
        f.writelines(labels)
        
    # 6. 컷아웃 (Cutout / 일부 가려짐 시뮬레이션 - 연기나 잔해물에 가려짐)
    cutout_img = img.copy()
    num_holes = 3
    for _ in range(num_holes):
        h, w = img.shape[:2]
        y = np.random.randint(0, h)
        x = np.random.randint(0, w)
        y1 = np.clip(y - h // 10, 0, h)
        y2 = np.clip(y + h // 10, 0, h)
        x1 = np.clip(x - w // 10, 0, w)
        x2 = np.clip(x + w // 10, 0, w)
        cutout_img[y1:y2, x1:x2] = 0 # 검은색 사각형으로 가림
        
    cv2.imwrite(str(TRAIN_IMG_DIR / f"{base_name}_cutout.jpg"), cutout_img)
    with open(TRAIN_LBL_DIR / f"{base_name}_cutout.txt", "w") as f:
        f.writelines(labels)
        
    # 7. Grayscale (야간 적외선 IR 카메라 느낌)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    cv2.imwrite(str(TRAIN_IMG_DIR / f"{base_name}_gray.jpg"), gray_bgr)
    with open(TRAIN_LBL_DIR / f"{base_name}_gray.txt", "w") as f:
        f.writelines(labels)

def main():
    print("🚀 2차 초정밀 물리적 데이터 증강(Advanced Augmentation) 시작...")
    img_files = list(TRAIN_IMG_DIR.glob("*.jpg"))
    original_count = len(img_files)
    
    if original_count == 0:
        print("❌ 증강할 원본 데이터가 없습니다.")
        return
        
    processed_count = 0
    for img_path in img_files:
        # 이전에 만든 1차 증강본은 건너뛰지 않고, 오히려 1차 증강본에까지 노이즈나 컷아웃을 적용해 폭발적으로 늘립니다.
        # 단, 무한루프 방지를 위해 이번 2차 증강 이름(noise, cutout, gray)이 들어간 것만 건너뜁니다.
        if "_" in img_path.stem and img_path.stem.split("_")[-1] in ["noise", "cutout", "gray"]:
            continue
            
        lbl_path = TRAIN_LBL_DIR / f"{img_path.stem}.txt"
        if lbl_path.exists():
            augment_image_and_label(img_path, lbl_path)
            processed_count += 1
            
    final_count = len(list(TRAIN_IMG_DIR.glob("*.jpg")))
    print(f"✅ 극강의 데이터 뻥튀기 완료! 현재 파일수 {original_count}장 -> 총 {final_count}장으로 급증!")

if __name__ == "__main__":
    main()
