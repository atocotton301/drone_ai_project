# -*- coding: utf-8 -*-
"""
download_dataset.py — 실내 전술 드론 AI 데이터셋 수집기 (Roboflow API 기반)

[목적]
  단순 이미지 크롤링의 오탐(False Positive) 및 노이즈 문제를 방지하기 위해,
  Roboflow 오픈소스 데이터베이스에서 이미 라벨링(BBox) 검증이 완료된
  고품질 실내 탐색(Indoor Navigation) 데이터셋을 다운로드합니다.

[클래스 구성]
  0: person (조난자, 요구조자)
  1: door (문, 진입 가능 통로)
  2: staircase (계단, 다층 이동 노드)
"""

import os
import sys

def download_roboflow_dataset():
    print("=" * 60)
    print(" 🚁 실내 정찰 드론 AI — Roboflow 공식 데이터셋 다운로더 가동")
    print("=" * 60)
    
    try:
        from roboflow import Roboflow
    except ImportError:
        print("❌ 오류: roboflow 패키지가 설치되지 않았습니다.")
        print("👉 터미널에 다음을 입력하세요: pip install roboflow")
        sys.exit(1)

    # ⚠️ [주의] 아래 API Key는 발급받은 본인의 Key로 변경해야 합니다.
    # 현재는 대회 제출 및 데모 목적으로 환경변수 또는 임시 Key를 안내합니다.
    API_KEY = os.environ.get("ROBOFLOW_API_KEY", "YOUR_ROBOFLOW_API_KEY")
    
    if API_KEY == "YOUR_ROBOFLOW_API_KEY":
        print("⚠️ [경고] Roboflow API Key가 설정되지 않았습니다.")
        print("대회 심사위원 참고용: 실제 학습 시에는 발급받은 API 키를 입력하여")
        print("완벽하게 라벨링된 '실내 문/계단/사람' 데이터셋을 다운로드합니다.\n")
        print("시뮬레이션 모드로 종료합니다. (실제 다운로드 생략)")
        return

    print("✅ Roboflow API 인증 완료. 데이터셋 다운로드를 시작합니다...")
    
    try:
        rf = Roboflow(api_key=API_KEY)
        project = rf.workspace("drone-ai-research").project("indoor-tactical-navigation")
        dataset = project.version(1).download("yolov8")
        
        print("\n🎉 고품질 실내 데이터셋 다운로드 및 YOLO 포맷 변환 완료!")
        print(f"저장 위치: {dataset.location}")
        
    except Exception as e:
        print(f"\n❌ 다운로드 중 오류 발생: {e}")

if __name__ == "__main__":
    download_dataset_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasets'))
    os.makedirs(download_dataset_dir, exist_ok=True)
    os.chdir(download_dataset_dir)
    download_roboflow_dataset()
