import json
import logging
import uuid
from datetime import timedelta

import boto3
import pytz
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.forms import model_to_dict
from django.utils import timezone
from django.utils.crypto import get_random_string
from drf_spectacular.utils import extend_schema_serializer
from pytz import timezone as pytztimezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import DateTimeField
from rest_framework.serializers import (
    BooleanField,
    CharField,
    IntegerField,
    UUIDField,
    ModelSerializer,
)

from config import settings
from . import enums, tasks, utils
from .models import (
    Playout,
    Distribution,
    Input,
    Channel,
    StateOptions,
    Clip,
    CallbackSubscriber,
    Action,
    Schedule,
    CallbackEvent,
    RawVideo,
    Vod,
    VodAsset,
)
from .utils import get_boto_client

logger = logging.getLogger(__name__)


class VeepsSerializer(object):
    @staticmethod
    def get_boto_client(resource_name):
        return get_boto_client(resource_name)


logger = logging.getLogger(__name__)


@extend_schema_serializer(
    exclude_fields=["id"],
)
class DistributionSerializer(ModelSerializer):
    """
    description: CDN configuraiton to output the video to users

    priceclass	string  example: price100   AWS Priceclass to use for distro
    hlsurl	string($url)                    url of HLS output - Can shorten this if needed
    clips	[clips]
    """

    class Meta:
        model = Distribution

        fields = ["price_class", "hls_url", "clips"]


class InputSerializer(ModelSerializer, VeepsSerializer):
    inbound_ip = CharField(read_only=True)
    playout_id = UUIDField()
    uri = CharField(required=False)
    input_type = CharField(required=False)
    name = CharField(required=False)
    protocol = CharField(required=False)
    port = CharField(required=False)
    encryption = BooleanField(required=False)
    whitelist_cidr = CharField(required=False)
    zixi_stream_id = CharField(required=False)
    stack_id = CharField(required=False)
    s3_url = CharField(required=False)
    loop = CharField(required=False)

    class Meta:
        model = Input
        fields = [
            "id",
            "playout_id",
            "name",
            "inbound_ip",
            "protocol",
            "port",
            "encryption",
            "whitelist_cidr",
            "input_type",
            "zixi_stream_id",
            "stack_id",
            "state",
            "uri",
            "s3_url",
            "loop",
        ]
        read_only_fields = ["id", "stack_id", "uri"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mediaconnect_client = self.get_boto_client("mediaconnect")

    def create(self, validated_data):
        # run the normal create for the object
        playout_id = validated_data.pop("playout_id")
        playout = Playout.objects.get(id=playout_id)
        validated_data["playout"] = playout

        channel_input = super().create(validated_data)
        channel_input.playout = playout
        channel_input.save()

        self.create_input(channel_input)

        # Return the Input object
        return channel_input

    @staticmethod
    def get_input_template(channel_input):
        # run cloudformation to create the input
        playout = channel_input.playout

        # Start with the channel template
        input_template = playout.channel_template

        for playout_input in playout.input.filter(playout=playout, initial_input=False).all():
            # then add on each input
            input_template = playout_input.input_template(input_template.template)

        return input_template

    def create_input(self, channel_input):
        input_template = self.get_input_template(channel_input)

        logger.info(f"Trying to create input: {channel_input.name}")

        # Create the input by updating the change set
        input_template.update_change_set()

    def update_state(self, channel_input, state):
        state_options = [a for a, b in StateOptions.choices]
        if state not in state_options:
            raise ValueError(f"{state} not in {state_options}")

        input_template = self.get_input_template(channel_input)

        channel_input.state = state
        channel_input.save()

        if state == StateOptions.ON:
            input_template.start()
        else:
            input_template.stop()

    def delete_input(self, channel_input):
        # run cloudformation to delete the input
        input_template = self.get_input_template(channel_input)
        logger.info(f"Trying to delete input: {channel_input.name}")

        # delete the input
        input_template.update_change_set()

    @staticmethod
    def destroy(instance):
        """
        This is particularly interesting as it needs to
        :param Input instance:
        :return: None
        """
        playout = instance.playout

        other_inputs = (
            Input.objects.filter(playout_id=playout.id).filter(initial_input=False).exclude(id=instance.id).all()
        )
        input_template = playout.channel_template

        for playout_input in other_inputs:
            input_template = playout_input.input_template(input_template.template)

        # apply the change set
        input_template.update_change_set()

        instance.delete()


class ChannelSerializer(ModelSerializer, VeepsSerializer):
    playout_id = IntegerField()
    current_video_input = InputSerializer()
    current_audio_input = InputSerializer()

    class Meta:
        model = Channel
        fields = [
            "name",
            "description",
            "state",
            "current_video_input",
            "current_audio_input",
            "preview",
            "playout_id",
        ]
        read_only_fields = ["id", "stack_id", "playout_id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.medialive_client = self.get_boto_client("medialive")

    def update_state(self, channel, state):
        state_options = [a for a, b in StateOptions.choices]
        if state not in state_options:
            raise ValueError(f"{state} not in {state_options}")

        if state == "on":
            self.start_channel(channel)
        else:
            self.stop_channel(channel)

    def update_input(self, channel, input_uuid):
        # Create a schedule to immediately switch the input

        input_obj = Input.objects.get(id=input_uuid)
        input_id = input_obj.input_template.get_input_id()

        response = self.medialive_client.batch_update_schedule(
            ChannelId=channel.channel_template.get_channel_id(),
            Creates={
                "ScheduleActions": [
                    {
                        "ActionName": "string",
                        "ScheduleActionStartSettings": {"ImmediateModeScheduleActionStartSettings": {}},
                        "ScheduleActionSettings": {
                            "InputSwitchSettings": {
                                "InputAttachmentNameReference": f"{input_id}",
                            }
                        },
                    }
                ]
            },
        )
        return response

    @staticmethod
    def start_channel(channel):
        channel_id = channel.channel_template.get_channel_id()
        if channel_id is not None:
            channel.start()
            channel.state = "on"
            channel.save()

    @staticmethod
    def stop_channel(channel):
        channel_id = channel.channel_template.get_channel_id()
        if channel_id is not None:
            channel.stop()
            channel.state = "off"
            channel.save()


class PlayoutSerializer(ModelSerializer, VeepsSerializer):
    distribution = DistributionSerializer

    class Meta:
        model = Playout
        read_only_fields = ["id", "status", "created_on", "distribution"]
        fields = ["resolution"] + read_only_fields

    def create(self, validated_data):
        # run the normal create for the object
        playout = super().create(validated_data)

        playout.channel = Channel.objects.create(
            description=f"MedialLive channel for {playout.id}",
            name=f"MediaLiveChannel{playout.id}".replace("-", ""),
        )
        playout.save()

        # Create input -- needs to be created before the channel to get the preview ids
        self.create_input(playout)

        # Create Channel
        self.create_channel(playout)

        # Return the playout object
        return playout

    def delete(self, instance):
        # Delete channel
        self.delete_channel(instance)

        # Delete distribution
        # self.delete_distribution(instance)

        # Delete the underlying instance
        instance.delete()

    @staticmethod
    def create_input(playout):
        channel_input = Input.objects.create(
            playout=playout,
            name=f"default input for {playout.id}",
            initial_input=True,
            protocol="srt",
            port="2000",
        )
        channel_input.save()
        return channel_input

    @staticmethod
    def delete_input(playout):
        pass

    @staticmethod
    def create_channel(playout):
        # run cloudformation to create distribution
        channel = playout.channel_template

        # Create the channel
        channel.create()

    @staticmethod
    def delete_channel(playout):
        if playout.channel_id is None:
            return

        logger.info(f"Trying to delete channel: {playout.channel_template.channel_name}")

        # Stop it, and the flow
        playout.channel.stop()
        # ChannelSerializer.stop_channel_input(playout.channel)

        for channel_input in playout.input.all():
            channel_input.template.stop()

        # Delete it
        playout.channel_template.delete()
        playout.channel.delete()

        # Delete the channel
        playout.channel = None
        playout.save()


class ActionSerializer(ModelSerializer, VeepsSerializer):
    class Meta:
        model = Action
        read_only_fields = ["id"]
        fields = [
            "action_type",
            "start_type",
            "input_attachment",
            "follow_ref_action",
            "follow_point",
            "fixed_start_time",
            "schedule",
        ] + read_only_fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.medialive_client = self.get_boto_client("medialive")

    def validate(self, attrs):
        if attrs.get("action_type") == Action.INPUT_SWITCH_ACTION_TYPE and not attrs.get("input_attachment"):
            raise ValidationError("'input_attachment' payload must be provided in case of 'input' switch action type")

        if attrs.get("start_type") == Action.FOLLOW_START_TYPE:
            if not attrs.get("follow_ref_action"):
                raise ValidationError("'follow_ref_action' payload must be provided in case of 'follow' start type")
            if not attrs.get("follow_point"):
                raise ValidationError("'follow_point' payload must be provided in case of 'follow' start type")

        if attrs.get("start_type") == Action.FIXED_START_TYPE:
            if not attrs.get("fixed_start_time"):
                raise ValidationError("'fixed_start_time' payload must be provided in case of 'fixed' start type")
            if attrs.get("fixed_start_time") < timezone.now() + timedelta(seconds=15):
                raise ValidationError("'fixed_start_time' must be at least 15 seconds in the future")

        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        action = Action.objects.create(**validated_data)
        input_template = action.playout.channel_template
        input_id = action.input_attachment.input_id(input_template.template)
        channel_id = action.channel.channel_template.get_channel_id()

        schedule_actions = []
        new_action_descriptor = {
            "ActionName": action.action_name,
            "ScheduleActionSettings": {},
            "ScheduleActionStartSettings": {},
        }
        if action.action_type == Action.INPUT_SWITCH_ACTION_TYPE:
            new_action_descriptor["ScheduleActionSettings"] = {
                "InputSwitchSettings": {
                    "InputAttachmentNameReference": f"{input_id}",
                }
            }
        if action.start_type == Action.IMMEDIATE_START_TYPE:
            new_action_descriptor["ScheduleActionStartSettings"] = {"ImmediateModeScheduleActionStartSettings": {}}
        elif action.start_type == Action.FIXED_START_TYPE:
            new_action_descriptor["ScheduleActionStartSettings"] = {
                "FixedModeScheduleActionStartSettings": {
                    "Time": action.fixed_start_time.astimezone(pytz.utc).isoformat()
                }
            }
        elif action.start_type == Action.FOLLOW_START_TYPE:
            new_action_descriptor["ScheduleActionStartSettings"] = {
                "FollowModeScheduleActionStartSettings": {
                    "FollowPoint": "START" if action.follow_point == Action.START_FOLLOW_POINT else "END",
                    "ReferenceActionName": action.follow_ref_action.action_name,
                }
            }

        schedule_actions.append(new_action_descriptor)

        self.medialive_client.batch_update_schedule(ChannelId=channel_id, Creates={"ScheduleActions": schedule_actions})
        return action

    def delete(self):
        action = self.instance
        channel_id = action.channel.channel_template.get_channel_id()

        self.medialive_client.batch_update_schedule(ChannelId=channel_id, Deletes={"ActionNames": [action.action_name]})

        action.delete()


class ScheduleSerializer(ModelSerializer, VeepsSerializer):
    actions_data = ActionSerializer(source="actions", many=True, read_only=True)

    class Meta:
        model = Schedule
        read_only_fields = ["id", "created_on", "actions"]
        fields = ["live_date", "actions_data"] + read_only_fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.medialive_client = self.get_boto_client("medialive")

    @transaction.atomic
    def delete(self):
        schedule = self.instance
        actions = Action.objects.filter(schedule_id=schedule.id).all()
        channel_id = schedule.channel.channel_template.get_channel_id()

        # delete actions in aws channel schedule
        self.medialive_client.batch_update_schedule(
            ChannelId=channel_id, Deletes={"ActionNames": [action.action_name for action in actions]}
        )

        for action in actions:
            action.delete()
        schedule.delete()


class ClipSerializer(ModelSerializer, VeepsSerializer):
    start_time = DateTimeField(input_formats=["U", "%Y-%m-%d %H:%M:%S"])
    end_time = DateTimeField(input_formats=["U", "%Y-%m-%d %H:%M:%S"])

    class Meta:
        model = Clip
        read_only_fields = ["id", "status", "asset_id"]
        fields = ["start_time", "end_time", "playout"] + read_only_fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mediapackage_client = self.get_boto_client("mediapackage")
        self.mediapackage_vod_client = self.get_boto_client("mediapackage-vod")

    @transaction.atomic
    def create(self, validated_data):
        clip = super().create(validated_data)

        # Create a harvesting job for clipping in media package
        client = boto3.client("mediapackage")
        response = client.create_harvest_job(
            StartTime=clip.start_time.astimezone(pytztimezone("US/Eastern")).isoformat(),
            EndTime=clip.end_time.astimezone(pytztimezone("US/Eastern")).isoformat(),
            Id=f"{clip.id}",
            OriginEndpointId=f"{clip.playout.channel_origin_endpoint_id}",
            S3Destination={
                "BucketName": settings.AWS_S3_VOD_CLIP_BUCKET_NAME,
                "ManifestKey": f"{clip.playout_id}/{clip.id}/index.m3u8",
                "RoleArn": f"arn:aws:iam::{settings.AWS_ACCOUNT_NUMBER}:role/MP_S3_ROLE",
            },
        )
        clip.status = response["Status"]
        clip.save()

        return clip

    def destroy(self):
        clip = self.instance

        # Delete asset in media package
        if clip.asset_id:
            self.mediapackage_vod_client.delete_asset(Id=f"{clip.asset_id}")

        clip.delete()

    def ingest_asset(self):
        clip = self.instance
        clip.asset_id = str(uuid.uuid4())

        # Create an ingest asset in media package
        response = self.mediapackage_vod_client.create_asset(
            Id=clip.asset_id,
            PackagingGroupId="VOD",
            SourceArn=f"arn:aws:s3:::{settings.AWS_S3_VOD_CLIP_BUCKET_NAME}/{clip.playout.id}/{clip.id}/index.m3u8",
            SourceRoleArn=f"arn:aws:iam::{settings.AWS_ACCOUNT_NUMBER}:role/MP_S3_ROLE",
        )
        clip.asset_id = response.get("Id")

        clip.save()

        # Register to CallbackEvent and invoke task to callback endpoints
        for subscriber in CallbackSubscriber.objects.all():
            event = CallbackEvent.objects.create(
                playout=clip.playout,
                subscriber=subscriber,
                event_type=CallbackEvent.EVENT_TYPE_CLIPPING_SUCCESS,
                object_id=clip.id,
                event_object=json.dumps(model_to_dict(clip), sort_keys=True, indent=1, cls=DjangoJSONEncoder),
            )
            tasks.call_webhook(event.id)

        return clip


class CallbackSubscriberSerializer(ModelSerializer):
    class Meta:
        model = CallbackSubscriber
        read_only_fields = ["id", "signing_secret", "created_on", "updated_on"]
        fields = ["endpoint", "retry_count"] + read_only_fields

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.signing_secret = f"{enums.WEBHOOK_SIGNING_SECRET_PREFIX}{get_random_string(50, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')}"
        instance.save()
        return instance


class RawVideoSerializer(ModelSerializer):
    file_path = serializers.SerializerMethodField()

    class Meta:
        model = RawVideo
        read_only_fields = ["id", "upload_finished_at", "file_size", "file_path"]
        fields = ["playout"] + read_only_fields

    def get_file_path(self, obj):
        return f"{settings.AWS_S3_VOD_INPUT_BUCKET_NAME}/{obj.file}"

    def get_presigned_url(self, playout):
        file = RawVideo(playout=playout, file=None)
        file.full_clean()
        file.save()

        upload_path = utils.file_generate_upload_path(file)

        """
        We are doing this in order to have an associated file for the field.
        """
        file.file = file.file.field.attr_class(file, file.file.field, upload_path)
        file.save()

        presigned_data = utils.s3_generate_presigned_post(file_path=upload_path)

        return {"id": file.id, **presigned_data}


class VodSerializer(ModelSerializer):
    original_video_data = RawVideoSerializer(source="original_video", read_only=True)

    class Meta:
        model = Vod
        read_only_fields = ["id"]
        fields = [
            "playout",
            "create_type",
            "original_video",
            "original_video_data",
            "user_meta_data",
            "input_video_s3_object_key",
            "hls_group",
            "file_group",
            "clip",
            "clip_hls_path",
        ] + read_only_fields


class VodAssetSerializer(ModelSerializer):
    class Meta:
        model = VodAsset
        read_only_fields = ["id"]
        fields = [
            "playout",
            "aws_id",
            "egress_endpoints",
            "packaging_group_id",
            "source_arn",
            "tags",
        ] + read_only_fields
