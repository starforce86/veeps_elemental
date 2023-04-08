import django_filters

from apps.api import models


class VodAssetFilter(django_filters.FilterSet):
    class Meta:
        model = models.VodAsset
        fields = ["aws_id"]


class VodFilter(django_filters.FilterSet):
    class Meta:
        model = models.Vod
        fields = ["create_type", "vodasset__aws_id"]


class RawVideoFilter(django_filters.FilterSet):
    class Meta:
        model = models.RawVideo
        fields = ["vod__vodasset__aws_id"]
