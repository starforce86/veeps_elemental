from troposphere import Template, Output, Join, GetAtt, medialive, Ref
from troposphere.mediaconnect import Flow, Source
from . import CloudFormationStackGeneric
from ..enums import ZIXI_PUSH, ZIXI_PULL


class MediaConnectFlowSourceInput(CloudFormationStackGeneric):
    def __init__(
        self,
        name,
        description,
        protocol,
        encryption,
        port,
        encryption_password=None,
        cidr="0.0.0.0/0",
        zixi_stream_id=None,
        stack_id=None,
    ):
        super().__init__()
        self.stack_name = name
        self.name = name
        self.description = description
        self.protocol = protocol
        self.port = port
        self.encryption = encryption
        self.encryption_password = encryption_password
        self.cidr = str(cidr)
        self.zixi_stream_id = zixi_stream_id  # it should be None if it is not zixi protocol
        self.template = self.create_template()
        self.stack_id = stack_id

    def create_template(self):
        t = Template()

        t.set_description(self.description)
        non_uuid_name = self.name.replace("-", "")

        if self.protocol in [ZIXI_PUSH, ZIXI_PULL]:
            # Only if it is a zixi stream we should pass the stream, otherwise CFN crashes
            flow = t.add_resource(
                Flow(
                    title=f"{non_uuid_name}Flow",
                    Name=f"{self.name}Flow",
                    Source=Source(
                        title=self.name,
                        Name=self.name,
                        Description=self.description,
                        IngestPort=self.port,
                        Protocol=self.protocol,
                        StreamId=self.zixi_stream_id,
                        WhitelistCidr=self.cidr,
                    ),
                )
            )
        else:
            flow = t.add_resource(
                Flow(
                    title=f"{non_uuid_name}Flow",
                    Name=f"{self.name}Flow",
                    Source=Source(
                        title=self.name,
                        Name=self.name,
                        Description=self.description,
                        IngestPort=self.port,
                        Protocol=self.protocol,
                        WhitelistCidr=self.cidr,
                    ),
                )
            )

        t.add_output(
            Output(
                "FlowSourceInput",
                Value=Join(
                    "",
                    [
                        f"{self.protocol}://",
                        GetAtt(flow, "Source.IngestIp"),
                        ":",
                        GetAtt(flow, "Source.SourceIngestPort"),
                    ],
                ),
            )
        )

        return t


class MediaLiveInputStatic(CloudFormationStackGeneric):
    def __init__(
        self,
        playout,
        description,
        input_id,
        base_template,
        s3_url,
        loop=False,
        password_param=None,
        stack_id=None,
    ):
        super().__init__()
        self.playout = playout
        self.input_id = input_id
        self.input_type = "MP4_FILE"
        self.stack_name = self.playout.channel.cloudformation_channel_name
        self.base_template = base_template
        self.description = description
        self.s3_url = s3_url
        self.password_param = password_param
        self.stack_id = stack_id
        self.loop = loop
        self.template = self.create_template()

    @property
    def input_id_alpha(self):
        return f"{self.input_id}".replace("-", "")

    def create_template(self):
        template = self.base_template

        source = medialive.InputSourceRequest(Url=self.s3_url)

        if self.password_param is not None:
            source = medialive.InputSourceRequest(PasswordParam=self.password_param, Url=self.s3_url)

        s3_input = template.add_resource(
            medialive.Input(
                f"{self.input_id_alpha}",
                Name=f"{self.input_id}",
                Tags={},
                Type=self.input_type,
                Sources=[source],
            )
        )

        if self.loop:
            source_end_behavior = "LOOP"
        else:
            source_end_behavior = "CONTINUE"

        # noinspection DuplicatedCode
        input_attachment = medialive.InputAttachment(
            InputAttachmentName=Ref(s3_input),
            InputId=Ref(s3_input),
            InputSettings=medialive.InputSettings(
                DeblockFilter="DISABLED",
                DenoiseFilter="DISABLED",
                FilterStrength=1,
                InputFilter="AUTO",
                Smpte2038DataPreference="IGNORE",
                SourceEndBehavior=source_end_behavior,
            ),
        )

        template.resources.get(f"MediaLiveChannel{self.playout.id}MediaLiveChannel".replace("-", "")).resource[
            "Properties"
        ]["InputAttachments"].append(input_attachment)

        template.add_output(
            [
                Output(
                    f"Input{self.input_id_alpha}Arn",
                    Value=GetAtt(s3_input, "Arn"),
                ),
            ]
        )

        return template

    def start(self):
        # Add compatibility with live inputs
        pass

    def stop(self):
        # Add compatibility with live inputs
        pass

    def get_input_id(self):
        return self.get_output_value(f"{self.input_id_alpha}Arn").split(":")[-1]
