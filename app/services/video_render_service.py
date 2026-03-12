# 자막 입혀진 이미지 여러 장을 ffmpeg로 이어붙여 mp4 영상으로 만듦

import os
import subprocess
import uuid


def create_video_from_images(image_paths, output_path, duration=2):

    if not image_paths:
        raise ValueError("영상으로 만들 이미지가 없습니다.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # ffmpeg concat용 임시 목록 파일 생성
    temp_list = f"temp_{uuid.uuid4().hex}.txt"

    try:
        # ffmpeg concat 포맷에 맞는 입력 파일 작성
        # 각 이미지 몇 초 보여줄지 지정
        # 마지막 이미지는 한 번 더 써줘야 ffmpeg에서 마지막 duration이 제대로 반영됨

        with open(temp_list, "w", encoding="utf-8") as f:
            for img in image_paths:
                f.write(f"file '{os.path.abspath(img)}'\n")
                f.write(f"duration {duration}\n")
            f.write(f"file '{os.path.abspath(image_paths[-1])}'\n")

        # ffmpeg 실행 명령
        command = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", temp_list,
            "-vf", "fps=30,format=yuv420p",
            "-pix_fmt", "yuv420p",
            output_path
        ]

        subprocess.run(command, check=True)

    # 끝나면 임시 txt 파일 삭제
    finally:
        if os.path.exists(temp_list):
            os.remove(temp_list)