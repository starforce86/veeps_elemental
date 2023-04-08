import logging

from django.urls import reverse
from rest_framework import status

from . import VeepsTestCase
from .factories import PlayoutFactory, ChannelFactory, InputFactory
from ..models import StateOptions

logger = logging.getLogger(__name__)


class ChannelTests(VeepsTestCase):
    def setUp(self):
        super().setUp()

        self.playout = PlayoutFactory()
        channel = ChannelFactory()
        channel.save()
        self.playout.channel = channel
        self.playout.save()

        input = InputFactory()
        input.playout = self.playout
        input.save()

        self.input_update_data = {
            "name": "testupdate",
            "protocol": "rtp",
            "port": 9000,
            "encryption": False,
            "cidr": "0.0.0.0/0",
            "zixi_stream_id": "",
            "encryption_password": "",
        }
        self.playout_data = {
            "resolution": "HD",
        }

    def test_channel(self):
        endpoint_url = reverse("channel-list")

        logging.info("======> List Channels API (GET {})".format(endpoint_url))
        list_response = self.client.get(endpoint_url)

        logging.info("=========> should return status code 200")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        logging.info("=========> should make sure that response is of array type")
        self.assertIsInstance(list_response.json(), dict)

        logging.info("=========> should make sure that response results list length match count field")
        results = list_response.json().get("results")
        self.assertEqual(len(results), list_response.json().get("count"))

        logging.info("=========> should make sure that response item has all required fields, and are correct")
        last_item = results[-1]
        # For some reason when using FactoryBoy, it converts the uuid to int. Need to double check with manual testing.
        self.assertEqual(last_item["playout_id"], self.playout.id.int)
        self.assertIn(last_item["state"], [StateOptions.OFF, StateOptions.ON])

        self.assertNotEqual(None, self.playout.id)
        endpoint_url = reverse("channel-detail", kwargs={"playout_id": self.playout.id})

        logging.info("======> Start Channel API (PATCH {})".format(endpoint_url))

        start_channel_response = self.client.patch(endpoint_url, data={"state": StateOptions.ON}, format="json")

        logging.info("=========> should return status code 200")
        self.assertEqual(start_channel_response.status_code, status.HTTP_200_OK)

        logging.info("=========> should make sure that response state field got updated as on")
        self.assertEqual(start_channel_response.json()["state"], StateOptions.ON)

        self.assertNotEqual(None, self.playout.id)
        endpoint_url = reverse("channel-detail", kwargs={"playout_id": self.playout.id})

        logging.info("======> Stop Channel API (PATCH {})".format(endpoint_url))

        stop_channel_response = self.client.patch(endpoint_url, data={"state": StateOptions.OFF}, format="json")

        logging.info("=========> should return status code 200")
        self.assertEqual(stop_channel_response.status_code, status.HTTP_200_OK)

        logging.info("=========> should make sure that response state field got updated as off")
        self.assertEqual(stop_channel_response.json()["state"], StateOptions.OFF)
