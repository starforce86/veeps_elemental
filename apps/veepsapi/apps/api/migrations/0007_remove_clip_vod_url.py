# Generated by Django 4.1 on 2022-11-23 10:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0006_rawvideo_alter_callbackevent_event_type_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="clip",
            name="vod_url",
        ),
    ]
