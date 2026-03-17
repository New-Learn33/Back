# Minimax Video-01 영상 생성 (이전 SVD 대체)

import os
import requests

# Minimax Video-01 — Replicate에서 사용 가능한 고품질 I2V 모델
MODEL_REF = "minimax/video-01"

MOTION_MAP = {
    "low": "subtle gentle motion, slow camera movement, minimal animation",
    "medium": "natural moderate motion, smooth camera movement, lively animation",
    "high": "dynamic energetic motion, dramatic camera movement, intense animation",
}


def generate_video_from_image(image_path: str, output_path: str, motion_intensity: str = "medium"):
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        raise ValueError("REPLICATE_API_TOKEN이 없습니다.")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"입력 이미지가 없습니다: {image_path}")

    import replicate
    client = replicate.Client(api_token=token)

    motion_desc = MOTION_MAP.get(motion_intensity, MOTION_MAP["medium"])

    # 이미지를 파일 객체로 전달
    with open(image_path, "rb") as image_file:
        output = client.run(
            MODEL_REF,
            input={
                "prompt": f"Animate this illustration with {motion_desc}. Keep the character consistent, maintain art style, smooth natural movement.",
                "first_frame_image": image_file,
                "prompt_optimizer": True,
            },
        )

    # Replicate 반환: URL 문자열 또는 FileOutput 객체
    file_output = output if isinstance(output, str) else output

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if hasattr(file_output, "read"):
        with open(output_path, "wb") as f:
            f.write(file_output.read())
    elif isinstance(file_output, str):
        response = requests.get(file_output)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
    else:
        raise ValueError(f"예상하지 못한 output 타입입니다: {type(file_output)}")

    return {
        "local_path": output_path,
        "video_url": file_output if isinstance(file_output, str) else getattr(file_output, "url", None),
    }
