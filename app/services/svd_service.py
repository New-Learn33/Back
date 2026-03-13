# SVD 영상 생성

import os
import requests
import replicate

# 모델 : christophy/stable-video-diffusion
MODEL_REF = "christophy/stable-video-diffusion:92a0c9a9cb1fd93ea0361d15e499dc879b35095077b2feed47315ccab4524036"

def generate_video_from_image(image_path: str, output_path: str):
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        raise ValueError("REPLICATE_API_TOKEN이 없습니다.")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"입력 이미지가 없습니다: {image_path}")

    client = replicate.Client(api_token=token)

    with open(image_path, "rb") as image_file:
        output = client.run(
            MODEL_REF,
            input={
                "input_image": image_file,
                "video_length": "14_frames_with_svd",
                "sizing_strategy": "maintain_aspect_ratio",
                "frames_per_second": 6,
                "motion_bucket_id": 127,
                "cond_aug": 0.02,
                "decoding_t": 14,
            },
        )

    file_output = output[0] if isinstance(output, list) else output

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 반환 타입이 파일 객체일 수도 있고 URL 문자열일 수도 있어서 둘 다 대응
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