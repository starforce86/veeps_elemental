import uuid

from troposphere import Template, Output, Tag, mediaconnect, medialive, GetAtt, Ref, Join
from troposphere.mediaconnect import Flow

from config import settings
from . import CloudFormationStackGeneric
from .channel import PreviewChannel

MEDIALIVE_INPUT_TYPES = [
    "UDP_PUSH",
    "RTP_PUSH",
    "RTMP_PUSH",
    "RTMP_PULL",
    "URL_PULL",
    "MP4_FILE",
    "MEDIACONNECT",
    "INPUT_DEVICE",
    "AWS_CDI",
    "TS_FILE",
]


class MediaConnectFlow(CloudFormationStackGeneric):
    def __init__(self, playout_id, description, whitelist_ip):
        super().__init__()
        self.playout_id = playout_id
        self.description = description
        self.whitelist_ip = whitelist_ip

    def create_template(self):
        t = Template()
        t.set_description(self.description)
        t.add_resource(
            Flow(
                f"{self.stack_name}MediaConnectFlow",
                Name="test-manual",
                Source={
                    "Description": "test",
                    "IngestIp": "18.209.37.245",
                    "IngestPort": 1243,
                    "Name": "test",
                    "MaxBitrate": 1000000,
                    "Protocol": "srt-listener",
                    "WhitelistCidr": self.whitelist_ip,
                },
                Tags={
                    Tag("playout", self.playout_id),
                },
            )
        )
        t.add_output(
            [
                Output(
                    "IngestIp",
                    Value="",
                ),
                Output(
                    "SourceArn",
                    Value="",
                ),
            ]
        )

        return t


class MediaLiveInputLive(CloudFormationStackGeneric):
    def __init__(
        self,
        playout,
        description,
        input_id,
        base_template,
        preview_mp_channel_id,
        preview_channel_id,
        preview_origin_endpoint_id,
        preview_origin_id,
        role_arn=f"arn:aws:iam::{settings.AWS_ACCOUNT_NUMBER}:role/MediaLiveAccessRole",
    ):
        super().__init__()
        self.playout = playout
        self.description = description
        self.role_arn = role_arn
        self.input_id = input_id
        self.stack_name = self.playout.channel.cloudformation_channel_name
        self.base_template = base_template
        self.input_type = "MEDIACONNECT"

        self.preview_mp_channel_id = preview_mp_channel_id
        self.preview_channel_id = preview_channel_id
        self.preview_origin_endpoint_id = preview_origin_endpoint_id
        self.preview_origin_id = preview_origin_id

        self.template = self.create_template()

    @property
    def input_id_alpha(self):
        return f"{self.input_id}".replace("-", "")

    def create_template(self):
        template = self.base_template

        channel_name = self.playout.channel.name

        max_bitrate = 200000000

        ingest_port = 2000
        whitelist_cidr = "0.0.0.0/0"

        flow_id = self.flow_name(self.input_id)
        source_id = uuid.uuid4()

        non_uuid_name = str(flow_id).replace("-", "")

        media_connect_flow_1 = template.add_resource(
            mediaconnect.Flow(
                f"{non_uuid_name}",
                Name=f"{flow_id}",
                Source=mediaconnect.Source(
                    Name=f"{source_id}",
                    Description=f"{source_id}",
                    IngestPort=ingest_port,
                    MaxBitrate=max_bitrate,
                    WhitelistCidr=whitelist_cidr,
                    Protocol="srt-listener",
                ),
                AvailabilityZone=GetAtt(f"{channel_name}subneta", "AvailabilityZone"),
            )
        )

        media_live_input = template.add_resource(
            medialive.Input(
                f"{self.input_id_alpha}",
                MediaConnectFlows=[
                    medialive.MediaConnectFlowRequest(
                        FlowArn=GetAtt(media_connect_flow_1, "FlowArn"),
                    ),
                ],
                Name=f"{self.input_id}",
                RoleArn=self.role_arn,
                Tags={
                    "Key": "Channel",
                    "Value": channel_name,
                },
                Type="MEDIACONNECT",
                DependsOn=[
                    media_connect_flow_1,
                ],
            )
        )

        input_attachment = medialive.InputAttachment(
            InputAttachmentName=Ref(media_live_input),
            InputId=Ref(media_live_input),
            InputSettings=medialive.InputSettings(
                DeblockFilter="DISABLED",
                DenoiseFilter="DISABLED",
                FilterStrength=1,
                InputFilter="AUTO",
                Smpte2038DataPreference="IGNORE",
                SourceEndBehavior="CONTINUE",
            ),
        )

        template.resources.get(f"MediaLiveChannel{self.playout.id}MediaLiveChannel".replace("-", "")).resource[
            "Properties"
        ]["InputAttachments"].append(input_attachment)

        template.add_output(
            [
                Output(
                    f"Input{self.input_id_alpha}Arn",
                    Value=GetAtt(media_live_input, "Arn"),
                ),
                Output(f"Input{self.input_id_alpha}SRTIP", Value=GetAtt(media_connect_flow_1, "Source.IngestIp")),
                Output(
                    f"Input{self.input_id_alpha}SRTPort", Value=GetAtt(media_connect_flow_1, "Source.SourceIngestPort")
                ),
                Output(
                    f"Input{self.input_id_alpha}FlowSourceInput",
                    Value=Join(
                        "",
                        [
                            "srt://",
                            GetAtt(media_connect_flow_1, "Source.IngestIp"),
                            ":",
                            GetAtt(media_connect_flow_1, "Source.SourceIngestPort"),
                        ],
                    ),
                ),
            ]
        )

        # ################
        # Add preview output to the template
        template = PreviewChannel(
            self.description,
            self.playout.channel.cloudformation_channel_name,
            template,
            f"{non_uuid_name}",
            media_connect_flow_1,
            self.preview_mp_channel_id,
            self.preview_channel_id,
            self.preview_origin_endpoint_id,
            self.preview_origin_id,
        ).template

        return template

    def start(self):
        client = self.get_boto_client("mediaconnect")
        client.start_flow(FlowArn=self.get_flow_arn())

    def stop(self):
        client = self.get_boto_client("mediaconnect")
        try:
            client.stop_flow(FlowArn=self.get_flow_arn())
        except:
            pass

    def get_srt_uri(self):
        return self.get_output_value(f"Input{self.input_id_alpha}FlowSourceInput")

    def get_srt_ip(self):
        return self.get_output_value(f"Input{self.input_id_alpha}SRTIP")

    def get_flow_arn(self):
        return self.get_output_value(f"Input{self.input_id_alpha}SRTPort")

    def get_input_id(self):
        return self.get_output_value(f"Input{self.input_id_alpha}Arn").split(":")[-1]

    def get_initial_input_id(self):
        return self.get_output_value("MediaLiveInitialInputArn").split(":")[-1]

    @staticmethod
    def flow_name(input_id):
        return f"flow-{input_id}"
