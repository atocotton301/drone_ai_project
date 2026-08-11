import os
import argparse
import subprocess
import urllib.request
import zipfile

def download_file(url, dest):
    print(f"Downloading {url} to {dest}...")
    urllib.request.urlretrieve(url, dest)
    print("Download complete.")

def extract_zip(zip_path, extract_to):
    print(f"Extracting {zip_path} to {extract_to}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print("Extraction complete.")

def download_coco_val2017(dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    images_url = "http://images.cocodataset.org/zips/val2017.zip"
    annotations_url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
    
    images_zip = os.path.join(dest_dir, "val2017.zip")
    ann_zip = os.path.join(dest_dir, "annotations.zip")
    
    if not os.path.exists(images_zip):
        download_file(images_url, images_zip)
    if not os.path.exists(ann_zip):
        download_file(annotations_url, ann_zip)
        
    extract_zip(images_zip, dest_dir)
    extract_zip(ann_zip, dest_dir)
    print("COCO val2017 download and extraction finished.")

def filter_coco_person(coco_dir, output_dir):
    print(f"Filtering 'person' class from COCO in {coco_dir} to {output_dir}...")
    # 필터링 로직 구현 (Mock)
    # 실제로는 json 파싱하여 person(id:1)인 이미지만 복사하고 YOLO 형식으로 라벨 변환
    os.makedirs(output_dir, exist_ok=True)
    print("COCO Person filtering complete (Mock).")

def download_dfire(dest_dir):
    print("D-Fire 데이터셋은 Kaggle 또는 Roboflow API를 통해 다운로드해야 합니다.")
    print("실행 예시 (Kaggle CLI가 설치된 경우):")
    print(f"kaggle datasets download -d dataclusterlabs/fire-and-smoke-dataset -p {dest_dir} --unzip")
    
    # Kaggle CLI가 설치되어 있고 인증되었다고 가정하고 실행 시도
    try:
        subprocess.run(["kaggle", "datasets", "download", "-d", "dataclusterlabs/fire-and-smoke-dataset", "-p", dest_dir, "--unzip"], check=True)
        print("D-Fire 다운로드 완료.")
    except Exception as e:
        print("Kaggle CLI 실행 실패. API 키가 없거나 Kaggle이 설치되지 않았습니다.")
        print(f"오류: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and filter COCO & D-Fire datasets")
    parser.add_argument("--dataset-dir", type=str, default="datasets/raw", help="Directory to save raw datasets")
    parser.add_argument("--skip-coco", action="store_true", help="Skip COCO download")
    args = parser.parse_args()

    print("=== 데이터셋 다운로드 및 필터링 시작 ===")
    
    if not args.skip_coco:
        coco_dir = os.path.join(args.dataset_dir, "coco")
        download_coco_val2017(coco_dir)
        filter_coco_person(coco_dir, os.path.join(args.dataset_dir, "..", "converted", "coco_person"))
        
    dfire_dir = os.path.join(args.dataset_dir, "dfire")
    os.makedirs(dfire_dir, exist_ok=True)
    download_dfire(dfire_dir)
    
    print("=== 다운로드 스크립트 실행 완료 ===")
