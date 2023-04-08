from django.urls import path, include
from rest_framework import routers

from .views import (
    PlayoutViewSet,
    DistributionViewSet,
    InputViewSet,
    ChannelViewSet,
    ClipViewSet,
    ScheduleViewSet,
    ActionViewSet,
    CallbackSubscriberViewSet,
    RawVideoViewSet,
    VodAssetViewSet,
    VodViewSet,
    MediaStoreViewSet,
    DownloadViewSet,
)
from .webhook_views import webhook_handler

router = routers.SimpleRouter()

router.register(r"playout", PlayoutViewSet, basename="playout")
router.register(r"distribution", DistributionViewSet, basename="distribution")
router.register(r"input", InputViewSet, basename="input")
router.register(r"channel", ChannelViewSet, basename="channel")
router.register(r"schedule", ScheduleViewSet, basename="schedule")
router.register(r"action", ActionViewSet, basename="action")
router.register(r"clip", ClipViewSet, basename="clip")
router.register(r"raw_video", RawVideoViewSet, basename="raw_video")
router.register(r"vod", VodViewSet, basename="vod")
router.register(r"vod_asset", VodAssetViewSet, basename="vod_asset")
router.register(r"mediastore", MediaStoreViewSet, basename="mediastore")
router.register(r"download", DownloadViewSet, basename="download")
router.register(r"webhook", CallbackSubscriberViewSet, basename="webhook")

urlpatterns = [
    path(r"", include(router.urls)),
    path(r"aws_webhook/", webhook_handler),
]
