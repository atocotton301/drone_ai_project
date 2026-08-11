import os
import cv2
import numpy as np

def create_sample_dataset(base_dir):
    """
    YOLO 학습을 위한 더미(Sample) 데이터셋을 생성합니다.
    """
    images_dir = os.path.join(base_dir, 'images', 'train')
    labels_dir = os.path.join(base_dir, 'labels', 'train')
    
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)
    
    print(f"더미 데이터셋 디렉토리 생성 완료: {base_dir}")
    print("더미 이미지 10장 생성 중...")

    for i in range(10):
        # 640x640 랜덤 컬러 이미지 생성
        color = np.random.randint(0, 255, (3,), dtype=int)
        img = np.ones((640, 640, 3), dtype=np.uint8)
        img[:] = color
        
        img_path = os.path.join(images_dir, f"sample_{i:03d}.jpg")
        cv2.imwrite(img_path, img)
        
        # 더미 라벨 생성 (0~3 클래스 랜덤, 박스 좌표는 임의 설정)
        label_path = os.path.join(labels_dir, f"sample_{i:03d}.txt")
        class_id = i % 4  # 0: person, 1: weapon, 2: fire, 3: smoke
        
        with open(label_path, 'w') as f:
            # YOLO format: class x_center y_center width height (normalized)
            f.write(f"{class_id} 0.5 0.5 0.4 0.4\n")
            
    print("성공적으로 더미 데이터 10장을 생성했습니다.")

if __name__ == "__main__":
    dataset_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasets', 'sample'))
    create_sample_dataset(dataset_dir)
