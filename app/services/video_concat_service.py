# 여러 개 영상 → 하나로 합치기

import os
import subprocess
import uuid


def concat_video_clips(video_paths: list[str], output_path: str):
    if not video_paths:
        raise ValueError("이어붙일 영상이 없습니다.")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    temp_list = f"temp_{uuid.uuid4().hex}.txt"

    try:
        with open(temp_list, "w", encoding="utf-8") as f:
            for path in video_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")

        command = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", temp_list,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-an",
            output_path
        ]

        subprocess.run(command, check=True)

    finally:
        if os.path.exists(temp_list):
            os.remove(temp_list)