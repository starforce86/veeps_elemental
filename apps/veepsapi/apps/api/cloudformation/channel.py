import logging
import uuid

import boto3
from botocore.exceptions import ClientError
from troposphere import (
    Template,
    GetAtt,
    mediaconnect,
    medialive,
    Ref,
    ec2,
    Select,
    Split,
    cloudfront,
    mediapackage,
    Output,
    Join,
    mediastore,
    Tags,
    Sub,
    cloudwatch,
)
from troposphere.mediapackage import StreamSelection

from config import settings
from . import CloudFormationStackGeneric
from .channel_defaults import audio_defaults, output_defaults, video_defaults
from .channel_defaults.dashboard import get_dashboard_body
from ..enums import DISTRIBUTION_ORIGIN_ENDPOINT_STARTOVER_WINDOW


logger = logging.getLogger(__name__)


class PreviewChannel(CloudFormationStackGeneric):
    def __init__(
        self,
        description,
        channel_name,
        channel_template,
        flow_name,
        flow_obj,
        preview_mp_channel_id,
        preview_channel_id,
        preview_origin_endpoint_id,
        preview_origin_id,
    ):
        super().__init__()
        self.description = description
        self.parent_channel_name = channel_name
        self.resolution = "SD"
        self.channel_template = channel_template
        self.flow_obj = flow_obj
        self.flow_name = flow_name
        self.media_live_client = boto3.client("medialive")

        self.preview_mp_channel_id = preview_mp_channel_id
        self.preview_channel_id = preview_channel_id
        self.preview_origin_endpoint_id = preview_origin_endpoint_id
        self.preview_origin_id = preview_origin_id

        self.template = self.create_template()

    @property
    def channel_name(self):
        input_name = self.flow_name.replace("-", "")
        return f"{input_name}Preview"

    def create_template(self):
        template = self.channel_template
        codec = "AVC"
        max_avc_bitrate = "MAX_20_MBPS"
        role_arn = f"arn:aws:iam::{settings.AWS_ACCOUNT_NUMBER}:role/MediaLiveAccessRole"

        preview_video_output = [
            output_defaults.output_preview,
        ]
        preview_video_descriptions = [
            video_defaults.video_description_preview,
        ]

        preview_audio_descriptions = [audio_defaults.audio_preview]

        mp_channel_preview = template.add_resource(
            # Create MediaPackage Channel
            mediapackage.Channel(
                self.channel_name,
                Id=self.preview_mp_channel_id,
            )
        )

        preview_media_live_input = template.add_resource(
            medialive.Input(
                f"{self.channel_name}MediaLiveInput",
                MediaConnectFlows=[
                    medialive.MediaConnectFlowRequest(
                        FlowArn=GetAtt(self.flow_obj, "FlowArn"),
                    ),
                ],
                Name=f"{self.channel_name}i",
                RoleArn=role_arn,
                Tags={
                    "Key": "Channel",
                    "Value": self.channel_name,
                },
                Type="MEDIACONNECT",
                DependsOn=[
                    self.flow_obj,
                ],
            )
        )

        preview_input_attachment = medialive.InputAttachment(
            InputAttachmentName=Ref(preview_media_live_input),
            InputId=Ref(preview_media_live_input),
            InputSettings=medialive.InputSettings(
                DeblockFilter="DISABLED",
                DenoiseFilter="DISABLED",
                FilterStrength=1,
                InputFilter="AUTO",
                Smpte2038DataPreference="IGNORE",
                SourceEndBehavior="CONTINUE",
            ),
        )

        channel_preview_destination = medialive.OutputDestination(
            Id="destinationPreview",
            MediaPackageSettings=[
                medialive.MediaPackageOutputDestinationSettings(
                    ChannelId=self.preview_channel_id,
                ),
            ],
        )

        mp_preview_endpoint = template.add_resource(
            # Create an origin endpoint that Cloudfront can use
            mediapackage.OriginEndpoint(
                f"{self.flow_name}EndpointPreview",
                Id=self.preview_origin_endpoint_id,
                ChannelId=self.preview_mp_channel_id,
                DependsOn=mp_channel_preview.title,
                HlsPackage=mediapackage.OriginEndpointHlsPackage(
                    StreamSelection=StreamSelection(
                        StreamOrder="VIDEO_BITRATE_DESCENDING"
                    )
                ),
                StartoverWindowSeconds=DISTRIBUTION_ORIGIN_ENDPOINT_STARTOVER_WINDOW,
            )
        )

        destination_preview = Select(2, Split("/", GetAtt(mp_preview_endpoint, "Url")))

        mp_preview_distribution = template.add_resource(
            # Create Cloudfront Distribution
            cloudfront.Distribution(
                f"{self.channel_name}Distribution",
                DistributionConfig=cloudfront.DistributionConfig(
                    Origins=[
                        cloudfront.Origin(
                            # Create new origin that Cloudfront can use
                            Id=self.preview_origin_id,
                            DomainName=destination_preview,
                            CustomOriginConfig=cloudfront.CustomOriginConfig(OriginProtocolPolicy="match-viewer"),
                        ),
                    ],
                    DefaultCacheBehavior=cloudfront.DefaultCacheBehavior(
                        TargetOriginId=self.preview_origin_id,
                        ForwardedValues=cloudfront.ForwardedValues(QueryString=False),
                        ViewerProtocolPolicy="allow-all",
                    ),
                    Enabled=True,
                    HttpVersion="http2",
                ),
                Tags=[
                    {
                        "Key": "Channel",
                        "Value": self.parent_channel_name,
                    },
                    {
                        "Key": "Input",
                        "Value": self.flow_name,
                    },
                    {
                        "Key": "mediapackage:cloudfront_assoc",
                        "Value": GetAtt(mp_channel_preview, "Arn"),
                    },
                ],
            )
        )

        preview_output_group = medialive.OutputGroup(
            Name=f"{self.resolution}_preview",
            OutputGroupSettings=medialive.OutputGroupSettings(
                MediaPackageGroupSettings=medialive.MediaPackageGroupSettings(
                    Destination=medialive.OutputLocationRef(DestinationRefId="destinationPreview")
                )
            ),
            Outputs=preview_video_output,
        )

        preview_channel = template.add_resource(
            medialive.Channel(
                f"{self.channel_name}mlc",
                Name=f"{self.channel_name}",
                ChannelClass="SINGLE_PIPELINE",
                Destinations=[channel_preview_destination],
                EncoderSettings=medialive.EncoderSettings(
                    AudioDescriptions=preview_audio_descriptions,
                    OutputGroups=[preview_output_group],
                    VideoDescriptions=preview_video_descriptions,
                    TimecodeConfig=medialive.TimecodeConfig(
                        Source="SYSTEMCLOCK",
                    ),
                ),
                InputAttachments=[preview_input_attachment],
                InputSpecification=medialive.InputSpecification(
                    Codec=codec,
                    MaximumBitrate=max_avc_bitrate,
                    Resolution=self.resolution,
                ),
                LogLevel="DISABLED",
                RoleArn=role_arn,
                DependsOn=[
                    mp_preview_distribution,
                ],
                Tags={
                    "Key": "Channel",
                    "Value": self.parent_channel_name,
                },
            )
        )

        template.add_output(
            [
                Output(f"{self.flow_name}ChannelPreviewArn", Value=GetAtt(preview_channel, "Arn")),
                Output(f"{self.flow_name}DistributionPreviewUrl", Value=GetAtt(mp_preview_endpoint, "Url")),
            ]
        )

        return template


class MediaLiveChannel(CloudFormationStackGeneric):
    """
    Create a MediaLive Channel
    """

    def __init__(
        self,
        description,
        channel_name,
        mp_channel_id,
        origin_endpoint_id,
        origin_id,
        preview_mp_channel_id,
        preview_channel_id,
        preview_origin_endpoint_id,
        preview_origin_id,
        resolution="HD",
    ):
        super().__init__()
        self.description = description
        self.stack_name = channel_name
        self.resolution = resolution
        self.mp_channel_id = mp_channel_id
        self.origin_endpoint_id = origin_endpoint_id
        self.origin_id = origin_id

        self.preview_mp_channel_id = preview_mp_channel_id
        self.preview_channel_id = preview_channel_id
        self.preview_origin_endpoint_id = preview_origin_endpoint_id
        self.preview_origin_id = preview_origin_id

        self.media_live_client = boto3.client("medialive")

        self.template = self.create_template()

    @property
    def channel_name(self):
        return self.stack_name.replace("-", "")

    @property
    def is_uhd(self):
        if self.resolution not in ["UHD", "HD"]:
            raise ValueError(f"{self.resolution} is not a valid resolution")
        return self.resolution == "UHD"

    def create_template(self):
        template = Template()
        template.set_description(self.description)

        role_arn = f"arn:aws:iam::{settings.AWS_ACCOUNT_NUMBER}:role/MediaLiveAccessRole"
        codec = "AVC"
        max_bitrate = 200000000

        if self.is_uhd:
            max_avc_bitrate = "MAX_50_MBPS"
        else:
            max_avc_bitrate = "MAX_20_MBPS"

        ingest_port = 2000
        whitelist_cidr = "0.0.0.0/0"

        ms_container = template.add_resource(
            mediastore.Container(
                f"MSC{self.channel_name}",
                ContainerName=f"MSC{self.channel_name}",
                AccessLoggingEnabled=True,
                Tags=Tags(
                    Key="Channel",
                    Value=self.channel_name,
                ),
                DeletionPolicy="Retain",
            )
        )

        mp_channel = template.add_resource(
            # Create MediaPackage Channel
            mediapackage.Channel(
                self.channel_name,
                Id=self.mp_channel_id,
            )
        )

        mp_endpoint_1 = template.add_resource(
            # Create an origin endpoint that Cloudfront can use
            mediapackage.OriginEndpoint(
                f"{self.channel_name}Endpoint1",
                Id=self.origin_endpoint_id,
                ChannelId=self.mp_channel_id,
                DependsOn=mp_channel.title,
                HlsPackage=mediapackage.OriginEndpointHlsPackage(
                    StreamSelection=StreamSelection(
                        StreamOrder="VIDEO_BITRATE_DESCENDING"
                    ),
                ),
                StartoverWindowSeconds=DISTRIBUTION_ORIGIN_ENDPOINT_STARTOVER_WINDOW,
            )
        )

        destination1 = Select(2, Split("/", GetAtt(mp_endpoint_1, "Url")))

        mp_distribution_1 = template.add_resource(
            # Create Cloudfront Distribution
            cloudfront.Distribution(
                f"{self.channel_name}Distribution1",
                DistributionConfig=cloudfront.DistributionConfig(
                    Origins=[
                        cloudfront.Origin(
                            # Create new origin that Cloudfront can use
                            Id=self.origin_id,
                            DomainName=destination1,
                            CustomOriginConfig=cloudfront.CustomOriginConfig(OriginProtocolPolicy="match-viewer"),
                        ),
                    ],
                    DefaultCacheBehavior=cloudfront.DefaultCacheBehavior(
                        TargetOriginId=self.origin_id,
                        ForwardedValues=cloudfront.ForwardedValues(QueryString=False),
                        ViewerProtocolPolicy="allow-all",
                    ),
                    Enabled=True,
                    HttpVersion="http2",
                ),
                Tags=[
                    {
                        "Key": "Channel",
                        "Value": self.channel_name,
                    },
                    {
                        "Key": "mediapackage:cloudfront_assoc",
                        "Value": GetAtt(mp_channel, "Arn"),
                    },
                ],
            )
        )

        ec2_vpc_1 = template.add_resource(
            ec2.VPC(
                f"{self.channel_name}vpc",
                CidrBlock="10.1.2.0/24",
                EnableDnsSupport=True,
                EnableDnsHostnames=False,
                InstanceTenancy="default",
                Tags=[
                    {
                        "Key": "Name",
                        "Value": f"{self.channel_name}vpc",
                    },
                    {
                        "Key": "Channel",
                        "Value": self.channel_name,
                    },
                ],
            )
        )

        ec2_vpc_1_subnet_a = template.add_resource(
            ec2.Subnet(
                f"{self.channel_name}subneta",
                AvailabilityZone="us-east-1a",
                CidrBlock="10.1.2.0/28",
                VpcId=Ref(ec2_vpc_1),
                MapPublicIpOnLaunch=False,
                Tags=[
                    {
                        "Key": "Name",
                        "Value": f"{self.channel_name}a",
                    },
                    {
                        "Key": "Channel",
                        "Value": self.channel_name,
                    },
                ],
            )
        )

        media_connect_flow_1 = template.add_resource(
            mediaconnect.Flow(
                f"{self.channel_name}flow1",
                Name=f"{self.channel_name}flow1",
                Source=mediaconnect.Source(
                    Name=f"{self.channel_name}flow1s",
                    Description=f"{self.channel_name}flow1s",
                    IngestPort=ingest_port,
                    MaxBitrate=max_bitrate,
                    WhitelistCidr=whitelist_cidr,
                    Protocol="srt-listener",
                ),
                AvailabilityZone=GetAtt(ec2_vpc_1_subnet_a, "AvailabilityZone"),
            )
        )

        media_live_input = template.add_resource(
            medialive.Input(
                f"{self.channel_name}MediaLiveInput",
                MediaConnectFlows=[
                    medialive.MediaConnectFlowRequest(
                        FlowArn=GetAtt(media_connect_flow_1, "FlowArn"),
                    ),
                ],
                Name=f"{self.channel_name}i",
                RoleArn=role_arn,
                Tags={
                    "Key": "Channel",
                    "Value": self.channel_name,
                },
                Type="MEDIACONNECT",
                DependsOn=[
                    media_connect_flow_1,
                ],
            )
        )

        audio_descriptions = [
            audio_defaults.audio_1,
            audio_defaults.audio_2,
            audio_defaults.audio_3,
            audio_defaults.audio_4,
            audio_defaults.audio_2eac3,
        ]
        output_list = [
            output_defaults.output1080p,
            output_defaults.output720p,
            output_defaults.output480p,
            output_defaults.output240p,
        ]
        mediastore_output_list = [output_defaults.mediastore_output1080p]

        video_descriptions = [
            video_defaults.video_description_1080p,
            video_defaults.video_description_720p,
            video_defaults.video_description_480p,
            video_defaults.video_description_240p,
        ]
        mediastore_descriptions = [video_defaults.mediastore_video_description_1080p]

        if self.is_uhd:
            # Append the audio_2eac3 settings
            audio_descriptions += [audio_defaults.audio_1eac3]

            # prepend 2160p to the outputs/descriptions
            output_list = [output_defaults.output2160p] + output_list
            mediastore_output_list = [output_defaults.mediastore_output2160p] + mediastore_output_list
            mediastore_descriptions = [video_defaults.mediastore_video_description_2160p] + mediastore_descriptions
            video_descriptions = [video_defaults.video_description_2160p] + video_descriptions

        channel_destination = medialive.OutputDestination(
            Id="destination1",
            MediaPackageSettings=[
                medialive.MediaPackageOutputDestinationSettings(
                    ChannelId=self.mp_channel_id,
                ),
            ],
        )

        mediastore_destination = medialive.OutputDestination(
            Id="mediaStoredestination1",
            Settings=[
                medialive.OutputDestinationSettings(
                    Url=Sub(
                        "mediastoressl://${EndpointSansProtocol}/out/index",
                        {
                            "EndpointSansProtocol": Select(
                                1,
                                Split("://", GetAtt(ms_container, "Endpoint")),
                            ),
                        },
                    ),
                ),
            ],
        )

        ms_output_group = medialive.OutputGroup(
            Name="MediaStore",
            OutputGroupSettings=medialive.OutputGroupSettings(
                HlsGroupSettings=medialive.HlsGroupSettings(
                    HlsCdnSettings=medialive.HlsCdnSettings(
                        HlsMediaStoreSettings=medialive.HlsMediaStoreSettings(
                            MediaStoreStorageClass="TEMPORAL",
                            NumRetries=10,
                            ConnectionRetryInterval=1,
                            RestartDelay=15,
                            FilecacheDuration=300,
                        ),
                    ),
                    InputLossAction="EMIT_OUTPUT",
                    Mode="LIVE",
                    Destination=medialive.OutputLocationRef(DestinationRefId="mediaStoredestination1"),
                )
            ),
            Outputs=mediastore_output_list,
        )

        output_group = medialive.OutputGroup(
            Name=self.resolution,
            OutputGroupSettings=medialive.OutputGroupSettings(
                MediaPackageGroupSettings=medialive.MediaPackageGroupSettings(
                    Destination=medialive.OutputLocationRef(DestinationRefId="destination1")
                )
            ),
            Outputs=output_list,
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

        media_live_channel = template.add_resource(
            medialive.Channel(
                f"{self.channel_name}MediaLiveChannel",
                Name=f"{self.channel_name}",
                ChannelClass="SINGLE_PIPELINE",
                Destinations=[channel_destination, mediastore_destination],
                EncoderSettings=medialive.EncoderSettings(
                    AudioDescriptions=audio_descriptions,
                    OutputGroups=[output_group, ms_output_group],
                    VideoDescriptions=video_descriptions + mediastore_descriptions,
                    TimecodeConfig=medialive.TimecodeConfig(
                        Source="SYSTEMCLOCK",
                    ),
                ),
                InputAttachments=[input_attachment],
                InputSpecification=medialive.InputSpecification(
                    Codec=codec,
                    MaximumBitrate=max_avc_bitrate,
                    Resolution=self.resolution,
                ),
                LogLevel="DISABLED",
                RoleArn=role_arn,
                DependsOn=[
                    mp_distribution_1,
                ],
                Tags={
                    "Key": "Channel",
                    "Value": self.channel_name,
                },
            )
        )

        """
        Add Media Package PackagingGroup
        It's needed for creating asset for clipped VOD playback
        """
        packaging_group = template.add_resource(
            mediapackage.PackagingGroup(
                Id=f"MediaPackagePackagingGroup{self.channel_name}", title="MediaPackageDefaultPackagingGroup"
            )
        )

        """
        Add Media Package PackagingConfiguration
        It's needed for creating asset for clipped VOD playback
        """
        packaging_configuration = template.add_resource(
            mediapackage.PackagingConfiguration(
                Id=f"MediaPackagePackagingConfiguration{self.channel_name}",
                title="MediaPackageDefaultPackagingConfiguration",
                PackagingGroupId=Select(1, Split("/", GetAtt(packaging_group, "Arn"))),
                # PackagingGroupId=GetAtt(packaging_group, "Arn"),
                HlsPackage=mediapackage.HlsPackage(HlsManifests=[mediapackage.HlsManifest()]),
            )
        )
        """
        Create dashboard
        """
        channel_id = Select(8, Split(":", GetAtt(media_live_channel, "Arn")))

        cw_dashboard = template.add_resource(
            cloudwatch.Dashboard(
                "CloudWatchDashboard2",
                DashboardName=f"Playout_{self.channel_name}",
                DashboardBody=get_dashboard_body(
                    channel_name=self.channel_name,
                    channel_id=channel_id,
                    region=settings.AWS_DEFAULT_REGION,
                    mediapackage_channel_uuid=self.mp_channel_id,
                    channel_hls_url=GetAtt(mp_endpoint_1, "Url"),
                ),
            )
        )

        distribution_url = Join(
            "/",
            [
                GetAtt(mp_distribution_1, "DomainName"),
                Select(2, Split("/", GetAtt(mp_endpoint_1, "Url"))),
            ],
        )

        template.add_output(
            [
                Output("ChannelArn", Value=GetAtt(media_live_channel, "Arn")),
                Output("FlowArn", Value=GetAtt(media_connect_flow_1, "FlowArn")),
                Output("SRTIP", Value=GetAtt(media_connect_flow_1, "Source.IngestIp")),
                Output("SRTPort", Value=GetAtt(media_connect_flow_1, "Source.SourceIngestPort")),
                Output("DistributionDomainName", Value=GetAtt(mp_distribution_1, "DomainName")),
                Output("DistributionUrl", Value=distribution_url),
                Output("MediapackageUrl", Value=GetAtt(mp_endpoint_1, "Url")),
                Output("DashboardId", Value=Ref(cw_dashboard)),
                Output(
                    "FlowSourceInput",
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
                Output(
                    "MediaLiveInitialInputArn",
                    Value=GetAtt(media_live_input, "Arn"),
                ),
                Output("MediaPackagePackagingGroupArn", Value=GetAtt(packaging_group, "Arn")),
                Output("MediaPackagePackagingConfigurationArn", Value=GetAtt(packaging_configuration, "Arn")),
            ]
        )

        # ################
        # Add preview output to the template
        template = PreviewChannel(
            self.description,
            self.channel_name,
            template,
            f"{self.channel_name}flow1",
            media_connect_flow_1,
            self.preview_mp_channel_id,
            self.preview_channel_id,
            self.preview_origin_endpoint_id,
            self.preview_origin_id,
        ).template

        return template

    def start(self):
        client = self.get_boto_client("medialive")
        client.start_channel(ChannelId=self.get_channel_id())

    def stop(self):
        try:
            channel_id = self.get_channel_id()
        except ClientError as ex:
            if "does not exist" in ex.response["Error"]["Message"]:
                return
            raise ex
        except Exception as ex:
            logger.error(f"Error with channel {ex}")
            raise ex

        client = self.get_boto_client("medialive")
        client.stop_channel(ChannelId=channel_id)

    def get_channel_id(self):
        return self.get_output_value("ChannelArn").split(":")[-1]

    def get_flow_arn(self):
        return self.get_output_value("FlowArn")

    def get_srt_uri(self):
        return self.get_output_value("FlowSourceInput")

    def get_srt_ip(self):
        return self.get_output_value("SRTIP")

    def get_distribution_uri(self):
        return self.get_output_value("DistributionUrl")
