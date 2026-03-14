import os
from app.core.r2_client import get_r2_client

R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_BASE_URL = os.getenv("R2_PUBLIC_BASE_URL")


def upload_local_file_to_r2(local_file_path: str, folder: str, filename: str, content_type: str):
    if not R2_PUBLIC_BASE_URL or not R2_BUCKET_NAME:
        raise Exception("R2 환경변수(R2_PUBLIC_BASE_URL, R2_BUCKET_NAME)가 설정되지 않았습니다.")

    s3 = get_r2_client()
    object_key = f"{folder}/{filename}"

    with open(local_file_path, "rb") as f:
        s3.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=object_key,
            Body=f,
            ContentType=content_type,
        )

    return {
        "key": object_key,
        "url": f"{R2_PUBLIC_BASE_URL}/{object_key}",
    }