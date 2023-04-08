from datetime import datetime
import boto3
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils.timezone import now
from django.views import View
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
)
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from django_filters import rest_framework as filters

from . import utils
from .filters import VodAssetFilter, VodFilter, RawVideoFilter
from .models import (
    Input,
    Channel,
    Schedule,
    Action,
    Clip,
    Playout,
    Distribution,
    CallbackSubscriber,
    RawVideo,
    Vod,
    VodAsset,
)
from .authentication import IsAdminOrShowRunner
from .serializers import (
    DistributionSerializer,
    PlayoutSerializer,
    ChannelSerializer,
    ScheduleSerializer,
    ActionSerializer,
    ClipSerializer,
    CallbackSubscriberSerializer,
    InputSerializer,
    RawVideoSerializer,
    VodSerializer,
    VodAssetSerializer,
)


class HomeViewSet(View):
    """
    Home screen currently reroutes to the schema swagger for easier development
    """

    http_method_names = ["get"]

    def get(self, request):
        return redirect("/api/schema/swagger")


class BaseViewSet(GenericViewSet):
    filter_backends = (filters.DjangoFilterBackend,)


class ChannelViewSet(BaseViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ChannelSerializer
    queryset = Channel.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrShowRunner]
    lookup_field = "playout_id"

    # noinspection PyMethodOverriding
    def get_object(self, playout_id):
        return get_object_or_404(self.queryset, playout__pk=playout_id)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object(kwargs.get("playout_id"))
        serializer = self.get_serializer(instance)

        data = request.data
        new_state = data.get("state", None)
        new_video_input = data.get("video_input", None)
        # new_audio_input = data.get("audio_input", None)

        serializer.update_state(instance, new_state)

        if new_video_input is not None:
            serializer.update_input(instance, new_video_input)
        # ##############################################################3
        # All done, returning back the channel serializer
        return Response(serializer.data, status=status.HTTP_200_OK)


class InputViewSet(BaseViewSet, CreateModelMixin, ListModelMixin, RetrieveModelMixin, DestroyModelMixin):
    serializer_class = InputSerializer
    queryset = Input.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrShowRunner]
    lookup_field = "playout_id"

    # noinspection PyMethodOverriding
    def get_object(self, playout_id):
        return self.queryset.filter(playout_id=playout_id).all()

    def partial_update(self, request, *args, **kwargs):
        instances = self.get_object(kwargs.get("playout_id"))
        input_id = request.data.get("input_id", None)

        if input_id is None:
            return Response({"error", "input_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        instance = instances.filter(id=input_id).first()
        if instance is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)

        data = request.data
        new_state = data.get("state", None)

        serializer.update_state(instance, new_state)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instances = self.get_object(kwargs.get("playout_id"))
        serialized = self.serializer_class(instances, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instances = self.get_object(kwargs.get("playout_id"))
        input_id = request.data.get("input_id")
        instance = instances.filter(id=input_id).first()
        if instance is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        self.serializer_class(instance=instance).destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PlayoutViewSet(BaseViewSet, CreateModelMixin, ListModelMixin, RetrieveModelMixin):
    serializer_class = PlayoutSerializer
    queryset = Playout.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrShowRunner]
    lookup_field = "playout_id"

    # noinspection PyMethodOverriding
    def get_object(self, playout_id):
        return get_object_or_404(self.queryset, pk=playout_id)

    def retrieve(self, request, *args, **kwargs):
        playout_id = kwargs.get("playout_id")
        instance = self.get_object(playout_id)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        playout_id = kwargs.get("playout_id")
        instance = self.get_object(playout_id)
        serializer = self.get_serializer(instance, data=request.data)
        serializer.delete(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScheduleViewSet(BaseViewSet, RetrieveModelMixin, DestroyModelMixin):
    serializer_class = ScheduleSerializer
    queryset = Schedule.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrShowRunner]
    lookup_field = "playout_id"

    # noinspection PyMethodOverriding
    def get_object(self, playout_id):
        return self.queryset.filter(channels__playout=playout_id).all()

    def retrieve(self, request, *args, **kwargs):
        instances = self.get_object(kwargs.get("playout_id"))
        serialized = self.get_serializer(instances, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instances = self.get_object(kwargs.get("playout_id"))
        schedule = instances.first()
        if schedule is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        self.get_serializer(schedule).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ActionViewSet(BaseViewSet, CreateModelMixin, DestroyModelMixin):
    serializer_class = ActionSerializer
    queryset = Action.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrShowRunner]
    lookup_field = "playout_id"

    # noinspection PyMethodOverriding
    def get_object(self, playout_id):
        return self.queryset.filter(schedule__channel__playout=playout_id).all()

    def create(self, request, *args, **kwargs):
        playout_id = request.data.get("playout_id")
        playout = get_object_or_404(Playout.objects, pk=playout_id)

        if not playout.channel:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"detail": "No channel associated with the playout"}
            )

        # if not exist schedule instance for playout, create schedule
        if not playout.channel.schedule:
            schedule_data = {"live_date": datetime.now()}
            schedule_serializer = ScheduleSerializer(data=schedule_data)
            schedule_serializer.is_valid(raise_exception=True)
            schedule = schedule_serializer.save()

            playout.channel.schedule = schedule
            playout.channel.save()

        action_data = request.data
        action_data.update({"schedule": playout.channel.schedule.pk})
        action_serializer = self.get_serializer(data=action_data)
        action_serializer.is_valid(raise_exception=True)
        action = action_serializer.save()
        return Response(ActionSerializer(action).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instances = self.get_object(kwargs.get("playout_id"))
        action_id = request.data.get("action_id")
        instance = instances.filter(id=action_id).first()
        if instance is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        self.serializer_class(instance).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DistributionViewSet(BaseViewSet):
    serializer_class = DistributionSerializer
    authentication_classes = [TokenAuthentication]
    queryset = Distribution.objects.all()
    permission_classes = [IsAdminOrShowRunner]
    lookup_field = "playout_id"

    # noinspection PyMethodOverriding
    def get_object(self, playout_id):
        return get_object_or_404(self.queryset, playout__pk=playout_id)

    def retrieve(self, request, playout_id):
        distribution = self.get_object(playout_id)
        serializer = self.serializer_class(distribution)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClipViewSet(BaseViewSet, CreateModelMixin, ListModelMixin, RetrieveModelMixin, DestroyModelMixin):
    serializer_class = ClipSerializer
    queryset = Clip.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminOrShowRunner]

    def create(self, request, *args, **kwargs):
        data = request.data

        # Support unix timestamps as well.
        start_time = data.get("start_time", now())
        end_time = data.get("end_time", now())

        # if it's an int, then we know it should be a unix timestamp
        if isinstance(start_time, int) or len(start_time) == 10:
            start_time = datetime.fromtimestamp(int(start_time))
            data["start_time"] = start_time

        if isinstance(end_time, int) or len(end_time) == 10:
            end_time = datetime.fromtimestamp(int(end_time))
            data["end_time"] = end_time

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(self.serializer_class(instance).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        clip = self.get_object()
        serializer = self.serializer_class(clip)
        serializer.destroy()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CallbackSubscriberViewSet(ModelViewSet):
    serializer_class = CallbackSubscriberSerializer
    queryset = CallbackSubscriber.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)


class RawVideoViewSet(BaseViewSet, CreateModelMixin, ListModelMixin, RetrieveModelMixin):
    serializer_class = RawVideoSerializer
    queryset = RawVideo.objects.filter(upload_finished_at__isnull=False)
    filterset_class = RawVideoFilter

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        presigned_data = serializer.get_presigned_url(**serializer.validated_data)
        return Response(data=presigned_data)


class VodViewSet(BaseViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = VodSerializer
    queryset = Vod.objects.all()
    filterset_class = VodFilter


class VodAssetViewSet(BaseViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = VodAssetSerializer
    queryset = VodAsset.objects.all()
    filterset_class = VodAssetFilter


class MediaStoreViewSet(BaseViewSet, RetrieveModelMixin):
    def retrieve(self, request, *args, **kwargs):
        playout = Playout.objects.get(pk=kwargs.get("pk"))
        client = boto3.client("mediastore")
        response = client.describe_container(ContainerName=f"MSCMediaLiveChannel{playout.id}".replace("-", ""))
        if response["ResponseMetadata"]["HTTPStatusCode"] != status.HTTP_200_OK:
            return response
        client = boto3.client(service_name="mediastore-data", endpoint_url=response.get("Container").get("Endpoint"))
        response = client.list_items(Path="out")
        if response["ResponseMetadata"]["HTTPStatusCode"] != status.HTTP_200_OK:
            return response
        return Response(data=response["Items"])


class DownloadViewSet(BaseViewSet):
    serializer_class = RawVideoSerializer

    @action(methods=["POST"], detail=False)
    def get_presigned_url(self, request, *args, **kwargs):
        bucket = request.data["s3_object_path"].split("/")[0]
        key = "/".join(request.data["s3_object_path"].split("/")[1:])
        presigned_url = utils.get_boto_client("s3").generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600,
        )

        return Response(data=presigned_url)
