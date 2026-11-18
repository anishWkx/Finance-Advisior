import os
from pathlib import Path

import boto3
from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BACKEND_DIR.parent

load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env", override=False)


def get_storage_client():
    required = [
        "AWS_ENDPOINT_URL_S3",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "AWS_S3_BUCKET",
    ]

    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise RuntimeError(
            "Object storage configuration is missing: "
            + ", ".join(missing)
        )

    return boto3.client(
        "s3",
        endpoint_url=os.environ["AWS_ENDPOINT_URL_S3"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ["AWS_REGION"],
    )


def upload_document(
    content: bytes,
    object_key: str,
    content_type: str = "application/octet-stream",
):
    client = get_storage_client()

    client.put_object(
        Bucket=os.environ["AWS_S3_BUCKET"],
        Key=object_key,
        Body=content,
        ContentType=content_type,
    )

    return object_key


def delete_document(object_key: str):
    client = get_storage_client()

    client.delete_object(
        Bucket=os.environ["AWS_S3_BUCKET"],
        Key=object_key,
    )
