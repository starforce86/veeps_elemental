import json
import logging
from datetime import datetime

import requests
from django.core.serializers.json import DjangoJSONEncoder
from django.forms import model_to_dict
from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from config import settings
from . import models, tasks, utils
from .cloudformation.liveinput import MediaLiveInputLive
from .serializers import ClipSerializer
from .models import Channel, Clip, Input, RawVideo, Playout, Vod, VodAsset

logger = logging.getLogger(__name__)


@api_view(["GET", "POST"])
@permission_classes([])
def webhook_handler(request):
    request_body = request.body.decode("utf-8")
    json_data = json.loads(request_body)

    if json_data.get("Type") == "SubscriptionConfirmation":
        subscribe_url = json_data.get("SubscribeURL", None)
        if subscribe_url is not None:
            requests.get(subscribe_url)
        return Response(status=status.HTTP_200_OK)

    subject = json_data.get("Subject")

    if subject == "AWS CloudFormation Notification":
        # Handle cloudformation notification
        return cloudformation_handler(json_data)
    else:
        message = json_data.get("Message")
        message_source = json.loads(message).get("source")
        if message_source == "aws.mediaconnect":
            # Handle media connect notification
            return mediaconnect_handler(json_data)
        elif message_source == "aws.medialive":
            # Handle media live notification
            return medialive_handler(json_data)
        elif message_source == "aws.mediapackage":
            # Handle media package notification
            return mediapackage_handler(json_data)
        elif message_source == "aws.mediaconvert":
            # Handle media convert notification
            return mediaconvert_handler(json_data)
        elif message_source == "aws.s3":
            # Handle s3 notification
            return s3_handler(json_data)

    return Response(status=status.HTTP_200_OK)


def mediapackage_handler(json_data):
    message = json.loads(json_data.get("Message"))
    detail_type = message.get("detail-type")
    detail = message.get("detail")

    if detail_type == "MediaPackage HarvestJob Notification":
        # Handle harvesting job notification
        harvest_job_id = message["detail"]["harvest_job"]["id"]
        clip = Clip.objects.get(id=harvest_job_id)
        if clip:
            clip.status = message["detail"]["harvest_job"]["status"]
            clip.save()

            if clip.status == "SUCCEEDED":
                s3_destination = message["detail"]["harvest_job"]["s3_destination"]
                Vod.objects.update_or_create(
                    playout=clip.playout,
                    create_type=Vod.CREATE_TYPE_HARVEST_JOB,
                    clip=clip,
                    defaults={
                        "playout": clip.playout,
                        "create_type": Vod.CREATE_TYPE_HARVEST_JOB,
                        "clip": clip,
                        "clip_hls_path": f"{s3_destination['bucket_name']}/{s3_destination['manifest_key']}",
                    },
                )

                # Create an ingest asset in media package
                clip_serializer = ClipSerializer(clip)
                clip_serializer.ingest_asset()
            elif clip.status == "FAILED":
                for subscriber in models.CallbackSubscriber.objects.all():
                    event = models.CallbackEvent.objects.create(
                        playout=clip.playout,
                        subscriber=subscriber,
                        event_type=models.CallbackEvent.EVENT_TYPE_CLIPPING_FAILED,
                        object_id=clip.id,
                        event_object=json.dumps(model_to_dict(clip), sort_keys=True, indent=1, cls=DjangoJSONEncoder),
                    )
                    tasks.call_webhook(event.id)
        else:
            logger.error(f"Could not find clip with id={harvest_job_id}")
    elif detail_type == "MediaPackage Input Notification" and detail and detail.get("event") == "IngestComplete":
        asset_id = message.get("resources")[0].split(":")[-1].split("/")[-1]
        response = utils.get_boto_client("mediapackage-vod").describe_asset(Id=asset_id)
        playout_id = response.get("SourceArn").split(":")[-1].split("/")[1]
        playout = Playout.objects.get(id=playout_id)
        if playout:
            vod_asset, created = VodAsset.objects.update_or_create(
                playout=playout,
                aws_id=asset_id,
                defaults={
                    "playout": playout,
                    "aws_id": asset_id,
                    "egress_endpoints": response.get("EgressEndpoints"),
                    "packaging_group_id": response.get("PackagingGroupId"),
                    "source_arn": response.get("SourceArn"),
                    "tags": response.get("Tags"),
                },
            )
            vod = Vod.objects.filter(playout=playout, clip__asset_id=asset_id).first()
            if vod:
                vod_asset.vod = vod
                vod_asset.save()
            vod = Vod.objects.filter(
                playout=playout,
                input_video_s3_object_key__contains="/".join(response.get("SourceArn").split(":")[-1].split("/")[1:3]),
            ).first()
            if vod:
                vod_asset.vod = vod
                vod_asset.save()

            # invoke vod_asset.ready callback notification
            for subscriber in models.CallbackSubscriber.objects.all():
                event = models.CallbackEvent.objects.create(
                    playout=vod_asset.playout,
                    subscriber=subscriber,
                    event_type=models.CallbackEvent.EVENT_TYPE_VOD_ASSET_READY,
                    object_id=vod_asset.id,
                    event_object=json.dumps(model_to_dict(vod_asset), sort_keys=True, indent=1, cls=DjangoJSONEncoder),
                )
                tasks.call_webhook(event.id)

    return Response(status=status.HTTP_200_OK)


def cloudformation_handler(json_data):
    raw_messages = json_data.get("Message").split("\n")
    messages = {}

    for message in raw_messages:
        msplit = message.split("=")
        if len(msplit) == 2:
            messages[msplit[0]] = msplit[1].replace("'", "")

    resource_status = messages.get("ResourceStatus")
    stack_name = messages.get("StackName")
    logical_resource = messages.get("LogicalResourceId")

    if "COMPLETE" in resource_status and stack_name == logical_resource:

        if "Stack" in messages.get("ResourceType"):
            channel = Channel.objects.filter(name=stack_name.replace("-", "")).first()
            channel_template = channel.channel_template

            srt_ip = channel_template.get_srt_ip()
            distribution_url = channel_template.get_distribution_uri()

            if channel is not None and "CREATE" in resource_status:
                # deal with the default input
                channel_input = channel.playout.get().input.filter(initial_input=True).first()
                channel_input.inbound_ip = srt_ip
                channel_input.save()

                channel.endpoint_url = distribution_url
                channel.created_on = now()
                channel.save()
                logger.info(f"Updated status of {stack_name}")

            # deal with the non-default input(s)
            inputs = channel.playout.get().input.filter(initial_input=False).all()

            for channel_input in inputs:
                channel_input.inbound_ip = channel_input.input_template(channel.channel_template.template).get_srt_ip()
                channel_input.save()

                logger.info(f"Updated input {channel_input.id}, {channel_input.inbound_ip}:{channel_input.port}")

            # deal with playout create result notification
            if (
                messages.get("ResourceType") == "AWS::CloudFormation::Stack"
                and resource_status == "CREATE_COMPLETE"
                and channel
            ):

                # update status field of playout instance
                channel.playout.get().status = resource_status
                channel.playout.get().save()

                # send notification to callback subscribers
                for subscriber in models.CallbackSubscriber.objects.all():
                    event = models.CallbackEvent.objects.create(
                        playout=channel.playout.get(),
                        subscriber=subscriber,
                        event_type=models.CallbackEvent.EVENT_TYPE_PLAYOUT_CREATED,
                        object_id=channel.id,
                        event_object=json.dumps(
                            model_to_dict(channel.playout.get()), sort_keys=True, indent=1, cls=DjangoJSONEncoder
                        ),
                    )
                    tasks.call_webhook(event.id)

    # get aws medialive channel id and store it into channel model for use when channel on/off notification
    # channel on/off notification frow aws has only this id in their message that can be used to find BE channel instance
    if messages.get("ResourceType") == "AWS::MediaLive::Channel" and resource_status == "CREATE_COMPLETE":
        aws_channel_name = json.loads(messages.get("ResourceProperties"))["Name"]
        channel = Channel.objects.filter(name=aws_channel_name).first()
        if channel:
            channel.aws_id = messages.get("PhysicalResourceId")
            channel.save()

    # update Input instance's aws_flow_arn field once media connect flow is created
    if messages.get("ResourceType") == "AWS::MediaConnect::Flow" and resource_status == "CREATE_COMPLETE":
        aws_flow_name = json.loads(messages.get("ResourceProperties"))["Name"]
        playout_id = messages.get("StackName").replace("MediaLiveChannel", "")
        non_initial_inputs = Input.objects.filter(playout_id=playout_id, initial_input=False).all()
        for input in non_initial_inputs:
            if MediaLiveInputLive.flow_name(input.id) == aws_flow_name:
                input.aws_flow_arn = messages.get("PhysicalResourceId")
                input.save()
                break
        initial_input = Input.objects.filter(playout_id=playout_id, initial_input=True).get()
        if aws_flow_name == f"MediaLiveChannel{initial_input.playout.id}flow1".replace("-", ""):
            initial_input.aws_flow_arn = messages.get("PhysicalResourceId")
            initial_input.save()

    # input create callback notification
    if messages.get("ResourceType") == "AWS::MediaLive::Input" and resource_status == "CREATE_COMPLETE":
        resource_properties = json.loads(messages.get("ResourceProperties"))
        if resource_properties.get("Type") == "MEDIACONNECT":
            input = Input.objects.filter(id=resource_properties.get("Name")).first()
            if input:
                for subscriber in models.CallbackSubscriber.objects.all():
                    event = models.CallbackEvent.objects.create(
                        playout=input.playout,
                        subscriber=subscriber,
                        event_type=models.CallbackEvent.EVENT_TYPE_INPUT_CREATED,
                        object_id=input.id,
                        event_object=json.dumps(
                            model_to_dict(input, exclude=["inbound_ip", "whitelist_cidr"]),
                            sort_keys=True,
                            indent=1,
                            cls=DjangoJSONEncoder,
                        ),
                    )
                    tasks.call_webhook(event.id)

    return Response(status=status.HTTP_200_OK)


def medialive_handler(json_data):
    message = json.loads(json_data.get("Message"))
    detail_type = message.get("detail-type")
    detail = message.get("detail")

    if detail_type == "MediaLive Channel State Change":
        # deal with channel on/off notification
        if detail.get("state") in ["RUNNING", "STOPPED"]:
            aws_channel_id = detail["channel_arn"].split(":")[-1]
            channel = Channel.objects.filter(aws_id=aws_channel_id).get()
            event_type = (
                models.CallbackEvent.EVENT_TYPE_CHANNEL_RUNNING
                if detail["state"] == "RUNNING"
                else models.CallbackEvent.EVENT_TYPE_CHANNEL_STOPPED
            )
            for subscriber in models.CallbackSubscriber.objects.all():
                event = models.CallbackEvent.objects.create(
                    playout=channel.playout.get(),
                    subscriber=subscriber,
                    event_type=event_type,
                    object_id=channel.id,
                    event_object=json.dumps(model_to_dict(channel), sort_keys=True, indent=1, cls=DjangoJSONEncoder),
                )
                tasks.call_webhook(event.id)

    return Response(status=status.HTTP_200_OK)


def mediaconnect_handler(json_data):
    message = json.loads(json_data.get("Message"))
    detail_type = message.get("detail-type")
    detail = message.get("detail")

    if detail_type == "MediaConnect Flow Status Change":
        # deal with input on/off notification
        if detail.get("currentStatus") in ["ACTIVE", "STANDBY"]:
            resource = message.get("resources")[0]
            input = Input.objects.filter(aws_flow_arn=resource).get()
            event_type = (
                models.CallbackEvent.EVENT_TYPE_INPUT_ACTIVE
                if detail["currentStatus"] == "ACTIVE"
                else models.CallbackEvent.EVENT_TYPE_INPUT_STANDBY
            )
            for subscriber in models.CallbackSubscriber.objects.all():
                event = models.CallbackEvent.objects.create(
                    playout=input.playout,
                    subscriber=subscriber,
                    event_type=event_type,
                    object_id=input.id,
                    event_object=json.dumps(
                        model_to_dict(input, exclude=["inbound_ip", "whitelist_cidr"]),
                        sort_keys=True,
                        indent=1,
                        cls=DjangoJSONEncoder,
                    ),
                )
                tasks.call_webhook(event.id)

    return Response(status=status.HTTP_200_OK)


def mediaconvert_handler(json_data):
    message = json.loads(json_data.get("Message"))
    detail_type = message.get("detail-type")
    detail = message.get("detail")

    if detail_type == "MediaConvert Job State Change" and detail.get("status") == "COMPLETE":
        raw_video_s3_uri = detail.get("userMetadata").get("input")
        playout_id = raw_video_s3_uri.replace("s3://", "").split("/")[1]
        playout = Playout.objects.get(id=playout_id)
        raw_video_suffix = "/".join(raw_video_s3_uri.replace("s3://", "").split("/")[1:])
        original_video = RawVideo.objects.filter(file=raw_video_suffix).first()
        if playout and original_video:
            vod, created = Vod.objects.update_or_create(
                playout=playout,
                create_type=Vod.CREATE_TYPE_MEDIA_CONVERT,
                original_video=original_video,
                defaults={
                    "playout": playout,
                    "create_type": Vod.CREATE_TYPE_MEDIA_CONVERT,
                    "original_video": original_video,
                    "user_meta_data": detail.get("userMetadata"),
                    "input_video_s3_object_key": "/".join(
                        detail.get("userMetadata").get("input").replace("s3://", "").split("/")[1:]
                    ),
                },
            )
            for outputGroupDetail in detail.get("outputGroupDetails"):
                if outputGroupDetail.get("type") == "HLS_GROUP":
                    vod.hls_group = outputGroupDetail
                    vod.save()
                elif outputGroupDetail.get("type") == "FILE_GROUP":
                    vod.file_group = outputGroupDetail
                    vod.save()

    return Response(status=status.HTTP_200_OK)


def s3_handler(json_data):
    message = json.loads(json_data.get("Message"))
    detail_type = message.get("detail-type")
    detail = message.get("detail")

    if (
        detail_type == "Object Created"
        and detail.get("bucket")
        and detail.get("bucket").get("name") == settings.AWS_S3_VOD_INPUT_BUCKET_NAME
    ):
        object_key_split = detail.get("object").get("key").split("/")
        object_key_prefix = object_key_split[0] + "/" + object_key_split[1]
        file_obj_key = f"{object_key_prefix}" + "/${filename}"
        file_obj = RawVideo.objects.filter(file=file_obj_key).first()
        if file_obj:
            file_obj.file = detail.get("object").get("key")
            file_obj.file_size = int(detail.get("object").get("size"))
            file_obj.upload_finished_at = datetime.now()
            file_obj.save()

            # trigger s3-vod-trigger lambda function
            # trigger this programmatically because the lambda is not triggered in case video is uploaded by api
            response = utils.get_boto_client("lambda").invoke(
                FunctionName=settings.AWS_VOD_S3_TRIGGER_LAMBDA_FUNCTION_NAME,
                InvocationType="RequestResponse",
                LogType="Tail",
                Payload=json.dumps(
                    {
                        "Records": [
                            {
                                "s3": {
                                    "object": {"key": detail.get("object").get("key")},
                                    "bucket": {"name": detail.get("bucket").get("name")},
                                }
                            }
                        ]
                    }
                ).encode(encoding="UTF-8"),
            )

    return Response(status=status.HTTP_200_OK)


class Response(Response):
    def __init__(self, data=None, status=None, template_name=None, headers=None, exception=False, content_type=None):
        super(Response, self).__init__(
            data=data or {"detail": ""},
            status=status,
            template_name=template_name,
            headers=headers,
            exception=exception,
            content_type=content_type,
        )
