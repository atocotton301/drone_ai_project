# -*- coding: utf-8 -*-
"""
download_dataset.py — 실내 전술 드론 AI 데이터셋 수집기 (Image Crawler)

[목적]
  Kaggle/Roboflow 링크 만료(404) 문제를 근본적으로 해결하기 위해,
  웹(Bing Images)에서 '실제 아파트 실내/복도/계단' 이미지를 직접 크롤링(수집)하여 
  학습의 원천 데이터(Raw Data)로 제공합니다.

[주의]
  수집된 이미지는 바운딩 박스(라벨)가 없는 원본(Raw) 상태이므로, 
  이 이미지들을 수집한 후 Roboflow나 CVAT 같은 라벨링 툴에 업로드하여 
  박스를 그리는 작업(Annotation)을 진행해야 완벽한 커스텀 데이터셋이 됩니다.
"""

import os, urllib.request, re, time
from pathlib import Path

RAW_DIR = Path("datasets/raw_images")

# 크롤링할 대상 키워드와 목표 수량 (각 30장씩 수집)
SEARCH_QUERIES = {
    "staircase": "한국 오래된 복도식 아파트 계단",
    "door": "한국 아파트 철문 현관문",
    "fire": "아파트 실내 화재 연기",
    "person": "아파트 복도 걷는 사람"
}
TARGET_COUNT = 30

def crawl_bing_images(query, dest_folder, count):
    print(f"\n🔍 검색 키워드: '{query}' -> {dest_folder.name} 폴더에 저장 중...")
    dest_folder.mkdir(parents=True, exist_ok=True)
    
    # Bing 이미지 검색 URL
    search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        req = urllib.request.Request(search_url, headers=headers)
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
    except Exception as e:
        print(f"❌ 검색 페이지 로드 실패: {e}")
        return

    # 정규식으로 이미지 URL 추출 (murl)
    img_urls = re.findall(r'murl&quot;:&quot;(.*?)&quot;', html)
    
    downloaded = 0
    for i, img_url in enumerate(img_urls):
        if downloaded >= count:
            break
            
        ext = "jpg"
        if ".png" in img_url.lower(): ext = "png"
        
        save_path = dest_folder / f"{dest_folder.name}_{downloaded:03d}.{ext}"
        
        try:
            req_img = urllib.request.Request(img_url, headers=headers)
            with urllib.request.urlopen(req_img, timeout=5) as response:
                save_path.write_bytes(response.read())
            print(f"  ✅ [{downloaded+1}/{count}] 다운로드 완료")
            downloaded += 1
            time.sleep(0.1) # 서버 부하 방지
        except:
            # 다운로드 실패(403 등) 시 조용히 넘어감
            pass

    print(f"🎯 '{query}' 수집 완료: 총 {downloaded}장 확보")

def main():
    print("=" * 60)
    print("  아파트 실내 드론 AI — 원천 이미지 크롤러 가동")
    print("=" * 60)
    
    for class_name, query in SEARCH_QUERIES.items():
        folder = RAW_DIR / class_name
        crawl_bing_images(query, folder, TARGET_COUNT)
        
    print("=" * 60)
    print("🎉 데이터 수집 완료!")
    print(f"수집된 이미지 경로: {RAW_DIR.absolute()}")
    print("\n[다음 단계]")
    print("1. 수집된 사진들 중 쓸모없는 사진이 섞여있다면 삭제하세요.")
    print("2. 남은 사진들을 Roboflow.com 등에 업로드하여 박스(라벨)를 그립니다.")
    print("3. Export한 ZIP 파일을 datasets/ 폴더에 넣고 학습을 시작하면 됩니다!")
    print("=" * 60)

if __name__ == "__main__":
    main()
