import os
import boto3
import uuid

def handler(event, context):

    packageGroupId = os.environ['PACKAGE_GROUP_ID']
    sourceRoleArn = os.environ['SOURCE_ROLE_ARN']

    filepath = event['detail']["outputGroupDetails"][0]['playlistFilePaths'][0]
    file_arn = filepath.replace("s3://", "arn:aws:s3:::")
    random_uuid = str(uuid.uuid4())

    vod = boto3.client('mediapackage-vod')
    response = vod.create_asset(
        Id=random_uuid,
        PackagingGroupId=packageGroupId,
        SourceArn=file_arn,
        SourceRoleArn=sourceRoleArn,
    )