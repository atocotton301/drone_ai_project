"""
train_jetson.py — Jetson Orin Nano Super 전용 YOLOv8 학습 + TensorRT 변환 스크립트

[용도]
  GitHub에서 이 프로젝트를 clone한 Jetson 보드에서 바로 실행합니다.
  1. 데이터셋 자동 다운로드 (없을 경우)
  2. YOLOv8n 커스텀 학습 (person / fire / smoke / weapon)
  3. 최적 모델 → ONNX → TensorRT (.engine) 자동 변환

[실행]
  python train_jetson.py
  python train_jetson.py --epochs 100 --batch 16

[결과]
  runs/detect/custom_train/weights/best.pt      — PyTorch 모델
  runs/detect/custom_train/weights/best.onnx    — ONNX 모델 (CPU 추론)
  runs/detect/custom_train/weights/best.engine  — TensorRT (Jetson GPU 가속)
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# ============================================================
# 설정
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATASET_YAML = BASE_DIR / "configs" / "custom_data.yaml"
DATASET_FINAL = BASE_DIR / "datasets" / "final"
PRETRAINED_MODEL = "yolov8n.pt"  # Ultralytics가 자동 다운로드
TRAIN_RUN_NAME = "custom_train"


def check_dataset():
    """datasets/final 폴더에 이미지가 있는지 확인. 없으면 다운로드 실행."""
    train_img_dir = DATASET_FINAL / "images" / "train"
    if not train_img_dir.exists() or not any(train_img_dir.iterdir()):
        print("⚠  datasets/final 폴더가 비어있습니다. 데이터셋을 자동으로 다운로드합니다...")
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "scripts" / "download_dataset.py")],
            cwd=BASE_DIR
        )
        if result.returncode != 0:
            print("❌ 데이터셋 다운로드 실패! 수동으로 실행하세요:")
            print("   python scripts/download_dataset.py")
            sys.exit(1)
    else:
        img_count = len(list(train_img_dir.glob("*")))
        print(f"✓ 데이터셋 확인 완료: Train 이미지 {img_count}장")


def patch_dataset_yaml():
    """
    custom_data.yaml의 path 항목을 현재 실행 환경에 맞게 동적으로 수정.
    Jetson(Linux) / PC(Windows) 모두 올바른 절대경로를 사용하도록 보장.
    """
    import yaml
    yaml_path = DATASET_YAML
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    correct_path = str(DATASET_FINAL).replace("\\", "/")
    if data.get("path") != correct_path:
        data["path"] = correct_path
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        print(f"  [YAML] dataset path 업데이트: {correct_path}")


def train(epochs: int, batch: int, imgsz: int, device: str):
    """YOLOv8 커스텀 학습 실행."""
    from ultralytics import YOLO

    print("\n" + "=" * 60)
    print(f"  🚀 YOLOv8n 커스텀 학습 시작")
    print(f"  Device : {device}")
    print(f"  Epochs : {epochs}")
    print(f"  Batch  : {batch}")
    print(f"  ImgSz  : {imgsz}")
    print(f"  Data   : {DATASET_YAML}")
    print("=" * 60 + "\n")

    model = YOLO(PRETRAINED_MODEL)

    results = model.train(
        data=str(DATASET_YAML),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        name=TRAIN_RUN_NAME,
        project="runs/detect",
        exist_ok=True,        # 이어서 학습 가능
        patience=20,          # 20 에포크 동안 개선 없으면 조기 종료
        save=True,
        plots=True,           # 학습 곡선 그래프 저장
        verbose=True,
        # 실내 탐지 최적화 설정
        hsv_h=0.015,          # 색조 증강 (화재/연기 색상 다양화)
        hsv_s=0.7,
        hsv_v=0.4,
        flipud=0.0,           # 드론 영상 특성상 상하 반전 없음
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
    )

    best_pt = Path(f"runs/detect/{TRAIN_RUN_NAME}/weights/best.pt")
    if not best_pt.exists():
        print("❌ 학습 실패: best.pt를 찾을 수 없습니다.")
        sys.exit(1)

    print(f"\n✅ 학습 완료! 최고 성능 모델: {best_pt}")
    return best_pt


def export_onnx(best_pt: Path, imgsz: int) -> Path:
    """best.pt → ONNX 변환."""
    from ultralytics import YOLO

    print("\n📦 ONNX 변환 중 (CPU 추론용)...")
    model = YOLO(str(best_pt))
    model.export(
        format="onnx",
        imgsz=imgsz,
        simplify=True,
        opset=12,             # TensorRT 호환 opset
    )
    onnx_path = best_pt.with_suffix(".onnx")
    print(f"✅ ONNX 변환 완료: {onnx_path}")
    return onnx_path


def export_tensorrt(best_pt: Path, imgsz: int) -> Path:
    """best.pt → TensorRT .engine 변환 (Jetson에서만 가능)."""
    from ultralytics import YOLO

    print("\n⚡ TensorRT 변환 중 (Jetson GPU 가속용)...")
    print("  ⏳ 최초 변환 시 3~10분 소요됩니다...")
    try:
        model = YOLO(str(best_pt))
        model.export(
            format="engine",
            imgsz=imgsz,
            half=True,        # FP16 — Jetson Orin에서 2x 속도
            simplify=True,
            workspace=4,      # GPU 메모리 4GB 할당
        )
        engine_path = best_pt.with_suffix(".engine")
        print(f"✅ TensorRT 변환 완료: {engine_path}")
        return engine_path
    except Exception as e:
        print(f"⚠  TensorRT 변환 실패 (비-Jetson 환경이거나 TensorRT 미설치): {e}")
        print("   ONNX 모델을 대신 사용하세요.")
        return None


def detect_device() -> str:
    """사용 가능한 디바이스 자동 감지."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"  🖥  GPU 감지: {gpu_name}")
            return "0"
        else:
            print("  💻 GPU 없음 → CPU 모드로 학습 (속도 느림)")
            return "cpu"
    except ImportError:
        return "cpu"


def main():
    parser = argparse.ArgumentParser(
        description="드론 AI 커스텀 학습 + TensorRT 변환 (Jetson용)"
    )
    parser.add_argument("--epochs", type=int, default=50,
                        help="학습 에포크 수 (기본: 50, Jetson 권장: 100)")
    parser.add_argument("--batch", type=int, default=8,
                        help="배치 크기 (Jetson Orin Nano 권장: 8~16)")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="학습 이미지 크기 (기본: 640)")
    parser.add_argument("--device", type=str, default="auto",
                        help="학습 디바이스: auto / 0 / cpu")
    parser.add_argument("--skip-tensorrt", action="store_true",
                        help="TensorRT 변환 건너뛰기 (PC 환경)")
    parser.add_argument("--skip-download", action="store_true",
                        help="데이터셋 다운로드 확인 건너뛰기")
    args = parser.parse_args()

    print("\n🚁 드론 AI 학습 파이프라인 시작\n")

    # 디바이스 결정
    device = detect_device() if args.device == "auto" else args.device

    # Step 0: YAML 경로 동적 패치 (Windows/Linux 호환)
    patch_dataset_yaml()

    # Step 1: 데이터셋 확인/다운로드
    if not args.skip_download:
        check_dataset()

    # Step 2: 학습
    best_pt = train(
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=device,
    )

    # Step 3: ONNX 변환
    onnx_path = export_onnx(best_pt, args.imgsz)

    # Step 4: TensorRT 변환 (Jetson에서만)
    if not args.skip_tensorrt:
        export_tensorrt(best_pt, args.imgsz)

    # 완료 요약
    print("\n" + "=" * 60)
    print("  ✅ 전체 파이프라인 완료!")
    print(f"  PT    : {best_pt}")
    print(f"  ONNX  : {onnx_path}")
    print(f"\n  다음 단계 (Jetson에서):")
    print(f"  python jetson/hardware_main.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
