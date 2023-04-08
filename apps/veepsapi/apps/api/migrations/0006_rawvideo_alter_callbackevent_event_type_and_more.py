# Generated by Django 4.1 on 2022-11-23 04:54

import apps.api.utils
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0006_input_loop_alter_channel_schedule"),
    ]

    operations = [
        migrations.CreateModel(
            name="RawVideo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(blank=True, null=True, upload_to=apps.api.utils.file_generate_upload_path)),
                ("file_size", models.IntegerField(blank=True, null=True)),
                ("upload_finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "playout",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name="raw_videos", to="api.playout"
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="callbackevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("playout.created", "playout.created"),
                    ("input.created", "input.created"),
                    ("channel.running", "channel.running"),
                    ("channel.stopped", "channel.stopped"),
                    ("clipping.success", "clipping.success"),
                    ("clipping.failed", "clipping.failed"),
                    ("vod_asset.ready", "vod_asset.ready"),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="channel",
            name="schedule",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="channels", to="api.schedule"
            ),
        ),
        migrations.CreateModel(
            name="VodAsset",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                        verbose_name="UUID",
                    ),
                ),
                ("aws_id", models.CharField(max_length=255)),
                ("egress_endpoints", models.JSONField(blank=True, null=True)),
                ("packaging_group_id", models.CharField(blank=True, max_length=255, null=True)),
                ("source_arn", models.CharField(blank=True, max_length=255, null=True)),
                ("tags", models.JSONField(blank=True, null=True)),
                (
                    "playout",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name="vod_assets", to="api.playout"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Vod",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                        verbose_name="UUID",
                    ),
                ),
                ("user_meta_data", models.JSONField(blank=True, null=True)),
                ("hls_group", models.JSONField(blank=True, null=True)),
                ("file_group", models.JSONField(blank=True, null=True)),
                (
                    "original_video",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name="vods", to="api.rawvideo"
                    ),
                ),
                (
                    "playout",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name="vods", to="api.playout"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
