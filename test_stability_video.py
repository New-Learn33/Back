"""
Stability AI Image-to-Video 테스트 스크립트
- 이미지 1장을 4초 영상으로 변환
- 이미지 요구사항: 1024x576, 576x1024, 또는 768x768
"""
import requests
import time
import os
from PIL import Image

STABILITY_API_KEY = "sk-4h81gPDLnFipFcuefyWe4n6amIPdSghQvZAc7Secsz3qPC04"
API_HOST = "https://api.stability.ai"

# 테스트할 이미지 (generated 폴더에서 첫 번째 이미지 사용)
GENERATED_DIR = os.path.join(os.path.dirname(__file__), "app", "static", "generated")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "app", "static", "videos")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def resize_for_stability(image_path: str, output_path: str) -> str:
    """Stability AI 요구사항에 맞게 이미지 리사이즈 (768x768)"""
    img = Image.open(image_path)
    img = img.resize((768, 768), Image.LANCZOS)
    img.save(output_path, "PNG")
    print(f"  리사이즈 완료: {img.size}")
    return output_path


def generate_video(image_path: str) -> str | None:
    """이미지를 영상으로 변환"""

    # 1단계: 리사이즈
    resized_path = image_path.replace(".png", "_resized.png")
    resize_for_stability(image_path, resized_path)

    # 2단계: 영상 생성 요청
    print("  영상 생성 요청 중...")
    with open(resized_path, "rb") as f:
        response = requests.post(
            f"{API_HOST}/v2beta/image-to-video",
            headers={"authorization": f"Bearer {STABILITY_API_KEY}"},
            files={"image": ("image.png", f, "image/png")},
            data={
                "seed": 0,
                "cfg_scale": 1.8,
                "motion_bucket_id": 127,
            },
        )

    if response.status_code != 200:
        print(f"  요청 실패: {response.status_code}")
        print(f"  응답: {response.text}")
        return None

    generation_id = response.json().get("id")
    print(f"  생성 ID: {generation_id}")

    # 3단계: 결과 폴링
    print("  영상 생성 대기 중...", end="", flush=True)
    while True:
        result = requests.get(
            f"{API_HOST}/v2beta/image-to-video/result/{generation_id}",
            headers={
                "authorization": f"Bearer {STABILITY_API_KEY}",
                "accept": "video/*",
            },
        )

        if result.status_code == 202:
            print(".", end="", flush=True)
            time.sleep(5)
            continue
        elif result.status_code == 200:
            print(" 완료!")
            output_path = os.path.join(OUTPUT_DIR, f"test_{generation_id}.mp4")
            with open(output_path, "wb") as f:
                f.write(result.content)
            print(f"  저장: {output_path}")
            return output_path
        else:
            print(f"\n  결과 조회 실패: {result.status_code}")
            print(f"  응답: {result.text}")
            return None


def main():
    # generated 폴더에서 이미지 하나 선택
    images = [f for f in os.listdir(GENERATED_DIR) if f.endswith(".png")]
    if not images:
        print("generated 폴더에 이미지가 없습니다.")
        return

    test_image = os.path.join(GENERATED_DIR, images[0])
    print(f"테스트 이미지: {images[0]}")

    video_path = generate_video(test_image)
    if video_path:
        print(f"\n성공! 영상 파일: {video_path}")
        print(f"브라우저에서 확인: http://localhost:8000/static/videos/{os.path.basename(video_path)}")
    else:
        print("\n영상 생성에 실패했습니다.")


if __name__ == "__main__":
    main()
