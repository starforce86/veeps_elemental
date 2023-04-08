import uuid

from django.contrib.auth.hashers import (
    check_password,
    make_password,
)
from django.core.validators import RegexValidator, MinLengthValidator
from django.db import models
from netfields import InetAddressField, CidrAddressField

from . import utils
from .cloudformation.channel import MediaLiveChannel
from .cloudformation.distribution import MediaPackageDistribution
from .cloudformation.liveinput import MediaLiveInputLive
from .cloudformation.staticinput import MediaLiveInputStatic
from .enums import INPUT_PROTOCOLS_CHOICES, INPUT_PROTOCOLS_URI_PREFIX

alphanumeric_validator = RegexValidator(r"^[0-9a-zA-Z]*$", "Only alphanumeric characters are allowed.")


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, editable=False, default=uuid.uuid4, verbose_name="UUID")

    class Meta:
        abstract = True


class CloudFormationModel(BaseModel):
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    submitted_on = models.DateTimeField(null=True, blank=True)
    stack_id = models.CharField(null=True, max_length=256)  # ARN Stack ID of the CloudFormation Model

    class Meta:
        abstract = True


class StateOptions(models.TextChoices):
    ON = ("on", "On")
    OFF = ("off", "Off")


class Clip(BaseModel):
    """
    description: Take a segment of a Livestrem and send it to VOD
    id	integer($int64)
    start_time	number example: 120.87  Start time of Livestream in seconds
    end_time	number  example: 3120.77    End time of Livestream in seconds
    status	string  example: IN_PROGRESS    Transcoding status (IN_PROGRESS, FINISHED, ERROR)
    asset_id	string($uuid)   VOD asset ID when in FINISHED state
    """

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50)
    asset_id = models.UUIDField(null=True)

    distribution = models.ForeignKey(
        "Distribution",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clips",
    )
    playout = models.ForeignKey(
        "Playout",
        on_delete=models.CASCADE,
        related_name="clips",
    )


class Schedule(BaseModel):
    live_date = models.DateTimeField(null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    @property
    def channel(self):
        return self.channels.get()


class Channel(CloudFormationModel):
    name = models.CharField(max_length=256, blank=True)
    description = models.TextField(blank=True)
    state = models.CharField(max_length=5, default=StateOptions.OFF, choices=StateOptions.choices)
    current_video_input = models.IntegerField(null=True)
    current_audio_input = models.IntegerField(null=True)
    schedule = models.ForeignKey(Schedule, null=True, on_delete=models.SET_NULL, related_name="channels")
    preview = models.URLField(null=True)
    endpoint_url = models.URLField(null=True, default=None)
    aws_id = models.CharField(max_length=16, null=True, blank=True)

    @property
    def playout_id(self):
        return self.playout.get().id

    @property
    def cloudformation_channel_name(self):
        return f"MediaLiveChannel{self.playout.get().id}"

    @property
    def channel_template(self):
        playout = self.playout.get()
        initial_input = Input.objects.filter(playout=playout, initial_input=True).first()

        channel = MediaLiveChannel(
            description=f"MedialLive channel for {playout.id}",
            channel_name=self.cloudformation_channel_name,
            resolution=playout.resolution,
            mp_channel_id=str(playout.channel_mp_channel_id),
            origin_endpoint_id=str(playout.channel_origin_endpoint_id),
            origin_id=str(playout.channel_origin_id),
            preview_mp_channel_id=str(initial_input.preview_mp_channel_id),
            preview_channel_id=str(initial_input.preview_channel_id),
            preview_origin_endpoint_id=str(initial_input.preview_origin_endpoint_id),
            preview_origin_id=str(initial_input.preview_origin_id),
        )
        return channel

    def update_state(self, new_state):
        if new_state not in StateOptions.choices:
            raise ValueError(f"{new_state} is not in {StateOptions.choices}")

    def start(self):
        self.channel_template.start()
        self.state = StateOptions.ON
        self.save()

    def stop(self):
        self.channel_template.stop()
        self.state = StateOptions.OFF
        self.save()


class Distribution(CloudFormationModel):
    name = models.CharField(max_length=256)
    description = models.TextField()
    hls_url = models.CharField(max_length=256)
    price_class = models.CharField(max_length=256, default="")
    mediapackage_id = models.UUIDField(null=True)
    cloudfront_id = models.CharField(max_length=256, null=True, blank=True)
    cloudformation_template = models.CharField(max_length=256, null=True, blank=True)

    @property
    def distribution_template(self):
        distribution = MediaPackageDistribution(
            description=f"MediaPackage distribution for {self.playout.get().id}",
            distribution_name=f"PlayoutDistribution{self.playout.get().id}",
        )
        return distribution


class Playout(BaseModel):
    """
    A livestreaming event
    """

    resolution = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    created_on = models.DateTimeField(auto_now_add=True)
    distribution = models.ForeignKey(Distribution, null=True, on_delete=models.SET_NULL, related_name="playout")
    channel = models.ForeignKey(Channel, null=True, on_delete=models.SET_NULL, related_name="playout")
    channel_mp_channel_id = models.UUIDField(default=uuid.uuid4)
    channel_origin_endpoint_id = models.UUIDField(default=uuid.uuid4)
    channel_origin_id = models.UUIDField(default=uuid.uuid4)

    @property
    def channel_template(self):
        return self.channel.channel_template

    @property
    def distribution_template(self):
        return self.distribution.distribution_template


class Input(CloudFormationModel):
    """
    A livestream input from camera or VOD in a specified format
    """

    class InputTypes(models.TextChoices):
        STATIC = "STATIC", "Static"
        LIVE = "LIVE", "Live"

    class StaticLoopTypes(models.TextChoices):
        CONTINUE = "CONTINUE", "Continue"
        LOOP = "LOOP", "Loop"

    name = models.CharField(max_length=128, null=True, validators=[alphanumeric_validator])
    inbound_ip = InetAddressField(null=True, help_text="Generated - This is the ip the camera will send data to")
    state = models.CharField(max_length=5, choices=StateOptions.choices, default=StateOptions.OFF)
    initial_input = models.BooleanField(default=False)
    protocol = models.CharField(
        choices=INPUT_PROTOCOLS_CHOICES,
        max_length=16,
        help_text="Which type of streaming protocol (SRT, RTP, ZIXI)",
    )
    port = models.IntegerField(default=0, help_text="If no port specified, the Default port for protocol will be used")
    encryption = models.BooleanField(default=False, help_text="Enable/disable encryption")
    whitelist_cidr = CidrAddressField(
        default="0.0.0.0/0",
        help_text="Whitelist the IP of the camera, all 0s is wide open",
    )
    zixi_stream_id = models.CharField(
        null=True,
        max_length=128,
        help_text="If protocol is zixi, this 'stream id' must " "match the 'stream id' on the device",
    )

    # "Use '[algo]$[salt]$[hexdigest]' as Django's auth password mechanism
    encryption_password = models.CharField(
        null=True,
        max_length=128,
        validators=[MinLengthValidator(4)],
        help_text="Optional - Encryption settings if enabled",
    )
    stack_id = models.CharField(null=True, max_length=256)
    playout = models.ForeignKey(Playout, on_delete=models.CASCADE, related_name="input")
    input_type = models.CharField(max_length=10, choices=InputTypes.choices, default=InputTypes.LIVE)
    s3_url = models.TextField(default="")
    aws_flow_arn = models.CharField(max_length=256, null=True, blank=True)
    loop = models.CharField(max_length=16, choices=StaticLoopTypes.choices, default=StaticLoopTypes.CONTINUE)

    preview_mp_channel_id = models.UUIDField(default=uuid.uuid4, null=True)
    preview_channel_id = models.UUIDField(default=uuid.uuid4, null=True)
    preview_origin_endpoint_id = models.UUIDField(default=uuid.uuid4, null=True)
    preview_origin_id = models.UUIDField(default=uuid.uuid4, null=True)
    # Stores the raw password if set_password() is called so that it can
    # be passed to password_changed() after the model is saved.
    _password = None

    @property
    def uri(self):
        uri_prefix = INPUT_PROTOCOLS_URI_PREFIX.get(self.protocol, "udp://")
        input_ip = "0.0.0.0"

        if self.inbound_ip is not None:
            input_ip = self.inbound_ip.ip.exploded

        return f"{uri_prefix}{input_ip}:{self.port}"

    @property
    def template(self):
        return self.playout.channel_template

    def input_template(self, base_template):
        if self.initial_input:
            return base_template

        if self.input_type.upper() == self.InputTypes.STATIC:
            input_template = MediaLiveInputStatic(self.playout, self.name, self.id, base_template, self.s3_url)
        else:
            input_template = MediaLiveInputLive(
                self.playout,
                self.name,
                self.id,
                base_template,
                preview_channel_id=str(self.preview_mp_channel_id),
                preview_origin_id=str(self.preview_origin_id),
                preview_mp_channel_id=str(self.preview_mp_channel_id),
                preview_origin_endpoint_id=str(self.preview_origin_endpoint_id),
            )

        return input_template

    def input_id(self, base_template):
        input_template = MediaLiveInputLive(
            self.playout,
            self.name,
            self.id,
            base_template,
            preview_channel_id=str(self.preview_mp_channel_id),
            preview_origin_id=str(self.preview_origin_id),
            preview_mp_channel_id=str(self.preview_mp_channel_id),
            preview_origin_endpoint_id=str(self.preview_origin_endpoint_id),
        )
        if self.initial_input:
            return input_template.get_initial_input_id()

        return input_template.get_input_id()

    def save(self, *args, **kwargs):
        is_newly_created = self._state.adding
        if is_newly_created:
            if self.encryption_password is not None:
                self.set_password(self.encryption_password)
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        self.encryption_password = make_password(raw_password)
        self._password = raw_password

    def check_password(self, raw_password):
        """
        Return a Boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """

        def setter(raw_password):
            self.set_password(raw_password)
            # Password hash upgrades shouldn't be considered password changes.
            self._password = None
            self.save(update_fields=["password"])

        return check_password(raw_password, self.encryption_password, setter)


class Action(BaseModel):
    INPUT_SWITCH_ACTION_TYPE = "input switch"
    ACTION_TYPES = ((INPUT_SWITCH_ACTION_TYPE, "Input Switch"),)

    FIXED_START_TYPE = "fixed"
    IMMEDIATE_START_TYPE = "immediate"
    FOLLOW_START_TYPE = "follow"
    START_TYPES = ((FIXED_START_TYPE, "Fixed"), (IMMEDIATE_START_TYPE, "Immediate"), (FOLLOW_START_TYPE, "Follow"))

    START_FOLLOW_POINT = "start"
    END_FOLLOW_POINT = "end"
    FOLLOW_POINT_TYPES = ((START_FOLLOW_POINT, "Start"), (END_FOLLOW_POINT, "End"))

    action_type = models.CharField(
        max_length=50,
        default=INPUT_SWITCH_ACTION_TYPE,
        choices=ACTION_TYPES,
    )
    start_type = models.CharField(
        max_length=50,
        choices=START_TYPES,
    )
    input_attachment = models.ForeignKey(Input, null=True, on_delete=models.SET_NULL)
    follow_point = models.CharField(
        max_length=50,
        choices=FOLLOW_POINT_TYPES,
        null=True,
    )
    follow_ref_action = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)
    fixed_start_time = models.DateTimeField(null=True)
    schedule = models.ForeignKey(Schedule, on_delete=models.PROTECT, related_name="actions")

    @property
    def playout(self):
        return self.schedule.channel.playout.get()

    @property
    def channel(self):
        return self.schedule.channel

    @property
    def action_name(self):
        return f"action-{self.id}"


class CallbackSubscriber(models.Model):
    """
    Endpoints subscribed to veepsapi events for callback
    """

    endpoint = models.URLField(max_length=200)
    retry_count = models.IntegerField(default=3)
    signing_secret = models.CharField(max_length=128, default="")

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "api_callback_subscriber"


class CallbackEvent(models.Model):
    """
    Veepsapi events to trigger callback for subscribers
    """

    # Playout events
    EVENT_TYPE_PLAYOUT_CREATED = "playout.created"

    # Input events
    EVENT_TYPE_INPUT_CREATED = "input.created"
    EVENT_TYPE_INPUT_ACTIVE = "input.active"
    EVENT_TYPE_INPUT_STANDBY = "input.standby"

    # Channel events
    EVENT_TYPE_CHANNEL_RUNNING = "channel.running"
    EVENT_TYPE_CHANNEL_STOPPED = "channel.stopped"

    # Clipping events
    EVENT_TYPE_CLIPPING_SUCCESS = "clipping.success"
    EVENT_TYPE_CLIPPING_FAILED = "clipping.failed"

    # VOD Asset events
    EVENT_TYPE_VOD_ASSET_READY = "vod_asset.ready"

    EVENT_TYPES = (
        (EVENT_TYPE_PLAYOUT_CREATED, EVENT_TYPE_PLAYOUT_CREATED),
        (EVENT_TYPE_INPUT_CREATED, EVENT_TYPE_INPUT_CREATED),
        (EVENT_TYPE_CHANNEL_RUNNING, EVENT_TYPE_CHANNEL_RUNNING),
        (EVENT_TYPE_CHANNEL_STOPPED, EVENT_TYPE_CHANNEL_STOPPED),
        (EVENT_TYPE_CLIPPING_SUCCESS, EVENT_TYPE_CLIPPING_SUCCESS),
        (EVENT_TYPE_CLIPPING_FAILED, EVENT_TYPE_CLIPPING_FAILED),
        (EVENT_TYPE_VOD_ASSET_READY, EVENT_TYPE_VOD_ASSET_READY),
    )

    playout = models.ForeignKey(Playout, on_delete=models.CASCADE, related_name="callback_events")
    subscriber = models.ForeignKey(CallbackSubscriber, on_delete=models.CASCADE, related_name="callback_events")
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
    )
    object_id = models.CharField(max_length=128, default="")
    event_object = models.TextField()
    retried_count = models.IntegerField(default=0)
    delivered_status = models.BooleanField(default=False)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "api_callback_event"


class CallbackLog(models.Model):
    """
    Logs of callback events triggered
    """

    playout_id = models.UUIDField()
    callback_endpoint = models.URLField(max_length=200)
    headers = models.TextField()
    body = models.TextField()
    response = models.TextField(null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    exception = models.TextField()
    execution_time = models.FloatField(null=True, blank=True)
    sig_timestamp = models.CharField(max_length=10, null=True, blank=True)
    sig_body = models.TextField(null=True, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "api_callback_log"


class RawVideo(models.Model):
    """
    Raw videos not converted by mediaconvert
    """

    playout = models.ForeignKey(Playout, on_delete=models.PROTECT, related_name="raw_videos")
    file = models.FileField(upload_to=utils.file_generate_upload_path, blank=True, null=True)
    file_size = models.IntegerField(null=True, blank=True)
    upload_finished_at = models.DateTimeField(blank=True, null=True)

    @property
    def is_valid(self):
        """
        We consider a file "valid" if the datetime flag has value.
        """
        return bool(self.upload_finished_at)


class Vod(BaseModel):
    """
    Both raw videos converted by mediaconvert and hls videos
    """

    CREATE_TYPE_MEDIA_CONVERT = "media_convert"
    CREATE_TYPE_HARVEST_JOB = "harvest_job"
    CREATE_TYPES = (
        (CREATE_TYPE_MEDIA_CONVERT, CREATE_TYPE_MEDIA_CONVERT),
        (CREATE_TYPE_HARVEST_JOB, CREATE_TYPE_HARVEST_JOB),
    )

    playout = models.ForeignKey(Playout, on_delete=models.PROTECT, related_name="vods")
    create_type = models.CharField(max_length=50, choices=CREATE_TYPES, null=True, blank=True)
    # following 4 fields are only valid if create_type is media_convert
    original_video = models.OneToOneField(RawVideo, null=True, blank=True, on_delete=models.PROTECT)
    user_meta_data = models.JSONField(null=True, blank=True)
    input_video_s3_object_key = models.CharField(max_length=512, null=True, blank=True)
    hls_group = models.JSONField(null=True, blank=True)
    file_group = models.JSONField(null=True, blank=True)
    # following 2 fields are only valid if create_type is harvest_job
    clip = models.OneToOneField(Clip, null=True, blank=True, on_delete=models.PROTECT)
    clip_hls_path = models.CharField(max_length=512, null=True, blank=True)


class VodAsset(BaseModel):
    playout = models.ForeignKey(Playout, on_delete=models.PROTECT, related_name="vod_assets")
    aws_id = models.CharField(max_length=255)
    vod = models.OneToOneField(Vod, null=True, blank=True, on_delete=models.PROTECT)
    egress_endpoints = models.JSONField(null=True, blank=True)
    packaging_group_id = models.CharField(max_length=255, null=True, blank=True)
    source_arn = models.CharField(max_length=255, null=True, blank=True)
    tags = models.JSONField(null=True, blank=True)
