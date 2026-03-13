import os
import textwrap
import subprocess
import uuid
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "fonts/NanumGothic.ttf"


def wrap_text(text: str, width: int = 18):
    return "\n".join(textwrap.wrap(text, width=width))


def create_subtitle_overlay(video_width: int, video_height: int, subtitle: str, overlay_path: str):
    if not os.path.exists(FONT_PATH):
        raise FileNotFoundError("폰트 파일이 존재하지 않습니다.")

    subtitle = wrap_text(subtitle, width=16)

    overlay = Image.new("RGBA", (video_width, video_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font = ImageFont.truetype(FONT_PATH, 28)

    box_height = int(video_height * 0.12)
    box_y = video_height - box_height

    # 아래 검정 반투명 박스
    draw.rectangle(
        [(0, box_y), (video_width, video_height)],
        fill=(0, 0, 0, 180)
    )

    bbox = draw.multiline_textbbox((0, 0), subtitle, font=font, spacing=10)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    text_x = (video_width - text_w) / 2
    text_y = box_y + (box_height - text_h) / 2

    draw.multiline_text(
        (text_x, text_y),
        subtitle,
        font=font,
        fill=(255, 255, 255, 255),
        spacing=10,
        align="center"
    )

    os.makedirs(os.path.dirname(overlay_path), exist_ok=True)
    overlay.save(overlay_path)


def get_video_size(input_path: str):
    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0:s=x",
        input_path
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    width, height = result.stdout.strip().split("x")
    return int(width), int(height)


def burn_subtitle_to_video(input_path: str, output_path: str, subtitle: str):
    if not os.path.exists(input_path):
        raise FileNotFoundError("입력 영상이 존재하지 않습니다.")

    width, height = get_video_size(input_path)

    temp_overlay = f"app/static/temp/subtitle_overlay_{uuid.uuid4().hex}.png"
    create_subtitle_overlay(width, height, subtitle, temp_overlay)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-i", temp_overlay,
        "-filter_complex", "overlay=0:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-an",
        output_path
    ]

    try:
        subprocess.run(command, check=True)
    finally:
        if os.path.exists(temp_overlay):
            os.remove(temp_overlay)