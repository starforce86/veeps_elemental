import logging
import time

from apps.api.cloudformation.channel import MediaLiveChannel
from django.test import TestCase

logger = logging.getLogger(__name__)


class TestMediaChannelObject(TestCase):
    def test_template(self):
        media_channel_template = MediaLiveChannel("MediaLiveChannelTest", "MediaLiveChannelTest")

        print(media_channel_template.template)
        self.assertNotEqual(media_channel_template.template, None)

        # try creating the template
        media_channel_template.create()

        while media_channel_template.get_status() not in ["CREATE_FAILED", "CREATE_COMPLETE"]:
            logger.info(f"Waiting... status {media_channel_template.get_status() }")
            time.sleep(10)

        # Adding another 10s wait, just for good measure.
        time.sleep(10)
        print(media_channel_template.get_status())

        # Delete the template
        media_channel_template.delete()

        while media_channel_template.get_status() not in ["DELETE_COMPLETE", "DELETE_FAILED"]:
            logger.info(f"Waiting... status {media_channel_template.get_status() }")
            time.sleep(10)

        print(media_channel_template.get_status())
