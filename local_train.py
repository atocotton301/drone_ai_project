"""
local_train.py — PC/로컬 환경에서 커스텀 데이터셋으로 빠른 학습 테스트

[용도]
  Jetson 보드 없이 로컬 PC에서 학습 파이프라인이 정상 동작하는지 검증합니다.
  GPU 있으면 GPU, 없으면 CPU로 자동 전환됩니다.

[실행]
  python local_train.py             # 기본 (5 에포크, 파이프라인 검증용)
  python local_train.py --epochs 30 # 30 에포크 로컬 학습

[전체 학습은 Jetson에서]
  Jetson에서: python train_jetson.py  (또는 ./jetson/setup_jetson.sh)
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Windows에서 OpenMP 라이브러리 충돌 방지 (torch + numpy 환경)
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

BASE_DIR = Path(__file__).resolve().parent
DATASET_YAML = BASE_DIR / "configs" / "custom_data.yaml"
DATASET_FINAL = BASE_DIR / "datasets" / "final"


def check_and_download_dataset():
    """데이터셋이 없으면 자동 다운로드."""
    train_dir = DATASET_FINAL / "images" / "train"
    if not train_dir.exists() or not any(train_dir.iterdir()):
        print("⚠  datasets/final 이 비어있습니다. 데이터셋 다운로드를 시작합니다...")
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "scripts" / "download_dataset.py")],
            cwd=BASE_DIR
        )
        if result.returncode != 0:
            print("❌ 데이터셋 다운로드 실패. 수동으로 실행하세요:")
            print("   python scripts/download_dataset.py")
            sys.exit(1)
    else:
        count = len(list(train_dir.glob("*")))
        print(f"✓ 데이터셋 확인: Train 이미지 {count}장")


def main():
    parser = argparse.ArgumentParser(description="로컬 PC에서 커스텀 YOLOv8 학습 테스트")
    parser.add_argument("--epochs", type=int, default=5, help="에포크 수 (기본: 5, 파이프라인 검증용)")
    parser.add_argument("--batch", type=int, default=8, help="배치 크기")
    parser.add_argument("--imgsz", type=int, default=640, help="이미지 크기")
    args = parser.parse_args()

    print("🚀 로컬 커스텀 학습 시작 (파이프라인 검증용)")
    print(f"   에포크: {args.epochs} | 배치: {args.batch} | 크기: {args.imgsz}")

    # 데이터셋 확인
    check_and_download_dataset()

    # 디바이스 감지
    try:
        import torch
        device = "0" if torch.cuda.is_available() else "cpu"
        print(f"   디바이스: {'GPU (' + torch.cuda.get_device_name(0) + ')' if device == '0' else 'CPU'}")
    except ImportError:
        device = "cpu"

    # 학습 실행
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")

    # YAML 경로 현재 환경에 맞게 패치
    import yaml
    with open(DATASET_YAML, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    correct_path = str(DATASET_FINAL).replace("\\", "/")
    if cfg.get("path") != correct_path:
        cfg["path"] = correct_path
        with open(DATASET_YAML, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)

    print(f"\n⏳ {args.epochs} 에포크 학습 중...")
    results = model.train(
        data=str(DATASET_YAML),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        name="custom_train",
        project="runs/detect",
        exist_ok=True,
        verbose=False,
    )

    # ONNX 변환
    best_pt = BASE_DIR / "runs" / "detect" / "custom_train" / "weights" / "best.pt"
    if best_pt.exists():
        print(f"\n✅ 학습 완료! → {best_pt}")
        print("📦 ONNX 변환 중...")
        model = YOLO(str(best_pt))
        model.export(format="onnx", imgsz=args.imgsz, simplify=True, opset=12)
        print(f"✅ ONNX 변환 완료: {best_pt.with_suffix('.onnx')}")
        print("\n💡 전체 학습(100 에포크)은 Jetson에서: python train_jetson.py")
    else:
        print("⚠  best.pt를 찾지 못했습니다.")


if __name__ == "__main__":
    main()
