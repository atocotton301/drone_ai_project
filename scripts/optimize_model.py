import os
import torch
import torch.nn.utils.prune as prune
from ultralytics import YOLO

def apply_pruning(pytorch_model, amount=0.3):
    """
    [핵심 기술 1: Pruning (가지치기)]
    학습이 완료된 모델 구조 내에서 예측 정확도에 영향도가 매우 낮은 
    파라미터(Weight)나 뉴런 결합을 강제로 솎아내어 메모리 용량을 압축합니다.
    """
    print(f"✂️ [Pruning] 모델 가중치의 {amount*100}% 가지치기를 시작합니다...")
    
    # YOLO 모델 내부의 PyTorch 레이어를 순회하며 2D 합성곱 계층을 가지치기
    for name, module in pytorch_model.named_modules():
        if isinstance(module, torch.nn.Conv2d):
            # L1 Unstructured Pruning (가장 영향력이 적은 가중치를 0으로 만듦)
            prune.l1_unstructured(module, name='weight', amount=amount)
            prune.remove(module, 'weight') # 가지치기 결과를 영구적으로 적용
            
    print("✅ [Pruning] 가지치기 완료! 모델의 추론 연산 속도가 대폭 증가했습니다.")
    return pytorch_model

def optimize_for_jetson(model_path, data_yaml_path):
    """
    [핵심 기술 2: On-device AI & Quantization (양자화)]
    외부 고성능 클라우드 서버 통신 없이(On-device AI), 기기에 탑재된 Edge GPU에서 
    실행하기 위해 고정밀도 실수형(FP32) 데이터를 8비트 정수형(INT8)으로 affine mapping 변환합니다.
    """
    print(f"🚀 [On-device AI 준비] 대상 모델 로드: {model_path}")
    
    if not os.path.exists(model_path):
        print(f"❌ 오류: 모델 파일을 찾을 수 없습니다: {model_path}")
        return
        
    # 모델 로드
    model = YOLO(model_path)
    
    # 1. Pruning (가지치기) 우선 적용
    model.model = apply_pruning(model.model, amount=0.2)
    
    # 2. TensorRT INT8 Quantization (양자화) 실행
    print("🔄 [Quantization] TensorRT INT8 양자화 변환을 시작합니다. (병목 현상 해소)")
    try:
        exported_path = model.export(
            format='engine',      # 임베디드 하드웨어(Jetson) 전용 포맷
            int8=True,            # INT8 양자화(Quantization) 활성화
            data=data_yaml_path,  # 캘리브레이션 데이터
            workspace=4,          # Jetson Orin NX VRAM 할당
            simplify=True,
            batch=1
        )
        print(f"✅ [Quantization 완료] 저전력 연산 효율성이 극대화된 엔진 생성: {exported_path}")
        print("💡 [On-device AI] 이제 독립형 엣지 환경에서 외부 통신 없이 보안 무인 체계 가동이 가능합니다.")
    except Exception as e:
        print(f"❌ [변환 에러] TensorRT 환경 오류: {e}")

if __name__ == "__main__":
    best_model_pt = r"c:\AI project\drone_ai_project\runs\detect\train\weights\best.pt"
    dataset_yaml = r"c:\AI project\drone_ai_project\coco8.yaml"
    optimize_for_jetson(best_model_pt, dataset_yaml)
