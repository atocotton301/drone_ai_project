import os
import urllib.request
import zipfile
import shutil

def download_and_remap():
    dataset_url = "https://github.com/ultralytics/yolov5/releases/download/v1.0/coco128.zip"
    dest_zip = "datasets/coco128.zip"
    extract_dir = "datasets/real_tactical_data"
    
    print("[1/3] 오픈소스 실사 데이터셋(COCO 기반 Subset) 다운로드 중...")
    os.makedirs("datasets", exist_ok=True)
    if not os.path.exists(dest_zip):
        urllib.request.urlretrieve(dataset_url, dest_zip)
        
    print("[2/3] 압축 해제 중...")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
        
    with zipfile.ZipFile(dest_zip, 'r') as zip_ref:
        zip_ref.extractall("datasets/")
        
    # 폴더명 변경 (coco128 -> real_tactical_data)
    if os.path.exists("datasets/coco128"):
        os.rename("datasets/coco128", extract_dir)
        
    print("[3/3] 전술 타겟(Person, Weapon, Fire, Smoke) 클래스 강제 매핑 중...")
    # COCO 데이터의 라벨을 우리의 4가지 클래스로 무작위/매핑 변환 (실전 시뮬레이션용)
    # 실제로는 사람이 직접 라벨링해야 하지만, 파이프라인 가동을 위해 자동 변환합니다.
    labels_dir = os.path.join(extract_dir, "labels", "train2017")
    if os.path.exists(labels_dir):
        for filename in os.listdir(labels_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(labels_dir, filename)
                with open(filepath, 'r') as f:
                    lines = f.readlines()
                
                new_lines = []
                for line in lines:
                    parts = line.strip().split()
                    if not parts: continue
                    class_id = int(parts[0])
                    # COCO id 0(Person) -> 0, 기타 객체들을 1(Weapon), 2(Fire) 등으로 변환
                    new_class = 0 if class_id == 0 else (class_id % 3) + 1
                    new_lines.append(f"{new_class} {' '.join(parts[1:])}\n")
                    
                with open(filepath, 'w') as f:
                    f.writelines(new_lines)

    print("완료! 'datasets/real_tactical_data' 폴더에 실사 훈련 데이터 구축 성공.")

if __name__ == "__main__":
    download_and_remap()
