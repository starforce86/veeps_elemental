import uuid

from troposphere import Template, Output, Join, GetAtt, Split, Select
from troposphere.cloudfront import (
    DistributionConfig,
    DefaultCacheBehavior,
    ForwardedValues,
    Distribution,
    Origin,
    CustomOriginConfig,
)
from troposphere.mediapackage import Channel, OriginEndpoint, OriginEndpointHlsPackage, StreamSelection

from . import CloudFormationStackGeneric


class MediaPackageDistribution(CloudFormationStackGeneric):
    """
    Class to create a MediaPackage Channel and corresponding Cloudfront Distribution
    """

    def __init__(self, description, distribution_name):
        super().__init__()
        self.description = description
        self.stack_name = distribution_name

        self.cloudformation_id = None
        self.channel_id = None
        self.origin_endpoint_id = None
        self.origin_id = None
        self.hls_url = None

        self.template = self.create_template()

    @property
    def distribution_name(self):
        return self.stack_name

    def create_template(self):
        t = Template()
        t.set_description(self.description)

        # Set uuids
        self.channel_id = str(uuid.uuid4())
        self.origin_endpoint_id = str(uuid.uuid4())
        self.origin_id = str(uuid.uuid4())

        # Start adding resources to the template
        mp_channel = t.add_resource(
            # Create MediaPackage Channel
            Channel(
                self.distribution_name,
                Id=self.channel_id,
            )
        )

        mp_endpoint = t.add_resource(
            # Create an origin endpoint that Cloudfront can use
            OriginEndpoint(
                f"{self.distribution_name}Endpoint",
                Id=self.origin_endpoint_id,
                ChannelId=self.channel_id,
                DependsOn=mp_channel.title,
                HlsPackage=OriginEndpointHlsPackage(
                    StreamSelection=StreamSelection(
                        StreamOrder="VIDEO_BITRATE_DESCENDING"
                    )
                ),

            )
        )

        mp_distribution = t.add_resource(
            # Create Cloudfront Distribution
            Distribution(
                f"{self.distribution_name}Distribution",
                DistributionConfig=DistributionConfig(
                    Origins=[
                        # Create new origin that Cloudfront can use
                        Origin(
                            Id=self.origin_id,
                            DomainName=Select(2, Split("/", GetAtt(mp_endpoint, "Url"))),
                            CustomOriginConfig=CustomOriginConfig(OriginProtocolPolicy="match-viewer"),
                        )
                    ],
                    DefaultCacheBehavior=DefaultCacheBehavior(
                        TargetOriginId=self.origin_id,
                        ForwardedValues=ForwardedValues(QueryString=False),
                        ViewerProtocolPolicy="allow-all",
                    ),
                    Enabled=True,
                    HttpVersion="http2",
                ),
            )
        )

        # Set distribution name so we can use it later
        self.hls_url = Join("", ["https://", GetAtt(mp_distribution, "DomainName")])
        self.cloudformation_id = GetAtt(mp_distribution, "Id")

        # Add the distribution name to the cloudfront output
        t.add_output(
            [
                Output(
                    "HLSURL",
                    Value=self.hls_url,
                ),
            ]
        )

        return t
