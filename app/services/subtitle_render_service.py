# 원본 이미지 1장을 받아서 아래쪽에 자막 박스를 깔고 텍스트 써서 새 이미지로 저장

import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "fonts/NanumGothic.ttf"

# 자막 길면 자동 줄바꿈
def wrap_text(text: str, width: int = 18):
    return "\n".join(textwrap.wrap(text, width=width))

# Pillow가 generated에 있는 원본 이미지를 읽어서 자막을 입힌 뒤 rendered 폴더에 새 파일로 저장
def render_subtitle_image(input_path: str, output_path: str, subtitle: str):

    if not os.path.exists(input_path):
        raise FileNotFoundError("입력 이미지가 존재하지 않습니다.")

    if not os.path.exists(FONT_PATH):
        raise FileNotFoundError("폰트 파일이 존재하지 않습니다.")

    # 원본 이미지 열기
    image = Image.open(input_path).convert("RGBA")
    width, height = image.size

    # 원본 이미지 위에 덮을 투명 레이어 생성 -> 여기에 자막 박스랑 텍스트 생성
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font = ImageFont.truetype(FONT_PATH, 40)

    subtitle = wrap_text(subtitle)

    box_height = int(height * 0.12)
    box_y = height - box_height

    # 자막 잘 보이게 검정 박스 생성
    draw.rectangle(
        [(0, box_y), (width, height)],
        fill=(0, 0, 0, 180)
    )

    bbox = draw.multiline_textbbox((0, 0), subtitle, font=font, spacing=10)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # 텍스트를 자막 박스 중앙에 오도록 위치 계산
    text_x = (width - text_w) / 2
    text_y = box_y + (box_height - text_h) / 2

    draw.multiline_text(
        (text_x, text_y),
        subtitle,
        font=font,
        fill=(255, 255, 255, 255),
        spacing=10,
        align="center"
    )

    result = Image.alpha_composite(image, overlay).convert("RGB")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 최종 자막 이미지 저장
    result.save(output_path)