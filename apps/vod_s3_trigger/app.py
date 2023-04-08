import json
import os
from urllib.parse import urlparse
import uuid
import boto3
import cv2

def getFirstMegabyteOfVideo(s3_bucket, s3_key):
    region = os.environ['AWS_DEFAULT_REGION']
    client = boto3.client('s3', region_name=region)

    start_byte = 0
    stop_byte = (1024 * 1024) - 1
    output_file = "/tmp/" + os.path.basename(s3_key)

    response = client.get_object(Bucket=s3_bucket, Key=s3_key, Range='bytes={}-{}'.format(start_byte, stop_byte))
    data = response['Body'].read()
    with open(output_file, 'wb+') as fd:
        fd.write(data)
    return output_file

def determineJobSettings(filename):
    video = cv2.VideoCapture(filename)
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return 'job-4k.json' if height == 2160 else 'job-hd.json'

def handler(event, context):
    s3_event = event['Records'][0]

    source_s3_key = s3_event['s3']['object']['key']
    source_s3_bucket = s3_event['s3']['bucket']['name']

    source_s3 = 's3://' + source_s3_bucket + '/' + source_s3_key
    source_s3_dirname = os.path.dirname(source_s3_key)

    initial_file = getFirstMegabyteOfVideo(source_s3_bucket, source_s3_key)
    job_settings_file = determineJobSettings(initial_file)
    os.remove(initial_file)

    job_name = 'Default'
    result_list = []
    result_code = 'Succeeded'
    result_string = 'The input video object was converted successfully.'

    # The type of output group determines which media players can play 
    # the files transcoded by MediaConvert.
    # For more information, see Creating outputs with AWS Elemental MediaConvert.
    output_group_type_dict = {
        'HLS_GROUP_SETTINGS': 'HlsGroupSettings',
        'FILE_GROUP_SETTINGS': 'FileGroupSettings',
        'CMAF_GROUP_SETTINGS': 'CmafGroupSettings',
        'DASH_ISO_GROUP_SETTINGS': 'DashIsoGroupSettings',
        'MS_SMOOTH_GROUP_SETTINGS': 'MsSmoothGroupSettings'
    }

    try:
        with open(job_settings_file) as file:
            job_settings = json.load(file)

        job_settings['Inputs'][0]['FileInput'] = source_s3

        # The path of each output video is constructed based on the values of 
        # the attributes in each object of OutputGroups in the job.json file. 
        destination_s3 = 's3://{0}/{1}' \
            .format(os.environ['DestinationBucket'],
                    source_s3_dirname)

        for output_group in job_settings['OutputGroups']:
            output_group_type = output_group['OutputGroupSettings']['Type']
            if output_group_type in output_group_type_dict.keys():
                output_group_type = output_group_type_dict[output_group_type]
                output_group['OutputGroupSettings'][output_group_type]['Destination'] = \
                    "{0}{1}".format(destination_s3,
                                    urlparse(output_group['OutputGroupSettings'][output_group_type]['Destination']).path)
            else:
                raise ValueError("Exception: Unknown Output Group Type {}."
                                 .format(output_group_type))

        job_metadata_dict = {
            'assetID': str(uuid.uuid4()),
            'application': os.environ['Application'],
            'input': source_s3,
            'settings': job_name
        }

        region = os.environ['AWS_DEFAULT_REGION']
        endpoints = boto3.client('mediaconvert', region_name=region).describe_endpoints()
        client = boto3.client('mediaconvert', region_name=region, 
                               endpoint_url=endpoints['Endpoints'][0]['Url'], 
                               verify=False)

        try:
            client.create_job(Role=os.environ['MediaConvertRole'], 
                              UserMetadata=job_metadata_dict, 
                              Settings=job_settings)
        # You can customize error handling based on different error codes that 
        # MediaConvert can return.
        # For more information, see MediaConvert error codes. 
        # When the result_code is TemporaryFailure, S3 Batch Operations retries 
        # the task before the job is completed. If this is the final retry, 
        # the error message is included in the final report.
        except Exception as error:
            result_code = 'TemporaryFailure'
            raise
    
    except Exception as error:
        if result_code != 'TemporaryFailure':
            result_code = 'PermanentFailure'
        result_string = str(error)

    finally:
        result_list.append({
            'resultCode': result_code,
            'resultString': result_string,
        })

    return {
        'results': result_list
    }
