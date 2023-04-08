from uuid import uuid4

import boto3

from config import settings


def get_boto_client(resource_name):
    return boto3.client(resource_name)


def file_generate_upload_path(instance):
    return f"{instance.playout.id}/{instance.id}/" + "${filename}"


def s3_generate_presigned_post(*, file_path):
    s3_client = boto3.client("s3")

    presigned_data = s3_client.generate_presigned_post(
        settings.AWS_S3_VOD_INPUT_BUCKET_NAME,
        file_path,
        ExpiresIn=settings.AWS_PRESIGNED_EXPIRY,
    )

    return presigned_data
