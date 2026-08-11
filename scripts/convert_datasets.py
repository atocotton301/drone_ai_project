import argparse
import os

def convert_dataset(input_dir, output_dir, dry_run=False):
    print(f"Converting dataset from {input_dir} to {output_dir}")
    if dry_run:
        print("[DRY RUN] No files will be modified.")
    
    # 1. COCO JSON -> YOLO 변환 로직 (Mock)
    # 2. Pascal VOC XML -> YOLO 변환 로직 (Mock)
    # 3. 클래스 번호 재매핑 및 통합
    # 4. 이미지 크기 확인 및 좌표 정규화
    
    print("Conversion finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert COCO/VOC dataset to YOLO format.")
    parser.add_argument("--input", type=str, required=True, help="Input directory")
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Run without modifying files")
    args = parser.parse_args()
    
    convert_dataset(args.input, args.output, args.dry_run)
